from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from web3 import Web3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="../frontend")
CORS(app)

# Configuration from .env file
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

print("Starting Donation DApp Backend for Sepolia...")
print(f"RPC URL: {RPC_URL}")
print(f"Contract Address: {CONTRACT_ADDRESS}")

# Connect to Sepolia
w3 = Web3(Web3.HTTPProvider(RPC_URL))
if w3.is_connected():
    print("Connected to Sepolia successfully")
    print(f"Current block: {w3.eth.block_number}")
else:
    print("Failed to connect to Sepolia")
    exit(1)

# Get account from private key
account = w3.eth.account.from_key(PRIVATE_KEY)
print(f"Using account: {account.address}")

# Check account balance
balance = w3.eth.get_balance(account.address)
balance_eth = w3.from_wei(balance, "ether")
print(f"Account balance: {balance_eth} ETH")

# Load contract ABI
try:
    with open("../artifacts/contracts/Donation.sol/Donation.json") as f:
        contract_json = json.load(f)
        abi = contract_json["abi"]
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
    print("Contract loaded successfully")

    # Verify contract owner
    owner = contract.functions.owner().call()
    print(f"Contract owner: {owner}")
    if owner.lower() == account.address.lower():
        print("You are the contract owner - withdraw function will work")
    else:
        print("You are not the contract owner - withdraw will fail")
except FileNotFoundError:
    print("Contract ABI file not found. Make sure you've compiled the contract.")
    exit(1)
except Exception as e:
    print(f"Error loading contract: {e}")
    exit(1)

@app.route("/")
def serve_frontend():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route("/")
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "network": "sepolia",
        "account": account.address,
        "contract": CONTRACT_ADDRESS,
        "balance": str(w3.from_wei(w3.eth.get_balance(account.address), "ether"))
    })

@app.route("/balance", methods=["GET"])
def get_balance():
    """Get contract balance in ETH"""
    try:
        balance_wei = contract.functions.getBalance().call()
        balance_eth = w3.from_wei(balance_wei, "ether")
        return jsonify({
            "balance": str(balance_eth),
            "balance_wei": str(balance_wei)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/contract-info", methods=["GET"])
def contract_info():
    """Get contract information"""
    try:
        owner = contract.functions.owner().call()
        total_donations_wei = contract.functions.totalDonations().call()
        total_donations_eth = w3.from_wei(total_donations_wei, "ether")
        balance_wei = contract.functions.getBalance().call()
        balance_eth = w3.from_wei(balance_wei, "ether")
        return jsonify({
            "address": CONTRACT_ADDRESS,
            "owner": owner,
            "total_donations": str(total_donations_eth),
            "current_balance": str(balance_eth),
            "network": "sepolia",
            "your_account": account.address
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/donate", methods=["POST"])
def donate():
    """Make a donation - backend signs the transaction"""
    try:
        data = request.get_json()
        if not data or "amount" not in data:
            return jsonify({"error": "Amount required"}), 400

        amount = data.get("amount")
        amount_float = float(amount)
        if amount_float <= 0:
            return jsonify({"error": "Amount must be positive"}), 400

        amount_wei = w3.to_wei(amount_float, "ether")

        # Check account balance
        account_balance = w3.eth.get_balance(account.address)
        if account_balance < amount_wei:
            return jsonify({
                "error": f"Insufficient funds. You have {w3.from_wei(account_balance, 'ether')} ETH, need {amount} ETH"
            }), 400

        # Build transaction
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.donate().build_transaction({
            "from": account.address,
            "value": amount_wei,
            "nonce": nonce,
            "gas": 200000,
            "gasPrice": w3.eth.gas_price
        })

        # Sign and send
        signed_tx = account.sign_transaction(tx)
        raw_tx = signed_tx.raw_transaction if hasattr(signed_tx, 'raw_transaction') else signed_tx.rawTransaction
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return jsonify({
            "status": "Donation successful",
            "amount": amount,
            "tx_hash": tx_hash.hex(),
            "block_number": receipt["blockNumber"],
            "from": account.address
        })
    except Exception as e:
        print(f"Error in donation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/withdraw", methods=["POST"])
def withdraw():
    """Withdraw funds - backend signs the transaction (owner only)"""
    try:
        # Check if caller is owner
        owner = contract.functions.owner().call()
        if account.address.lower() != owner.lower():
            return jsonify({
                "error": "Only owner can withdraw",
                "owner": owner,
                "your_account": account.address
            }), 403

        # Check balance
        balance_wei = contract.functions.getBalance().call()
        if balance_wei == 0:
            return jsonify({"error": "Contract balance is 0"}), 400

        # Build transaction
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.withdraw().build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 100000,
            "gasPrice": w3.eth.gas_price
        })

        # Sign and send
        signed_tx = account.sign_transaction(tx)
        raw_tx = signed_tx.raw_transaction if hasattr(signed_tx, 'raw_transaction') else signed_tx.rawTransaction
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return jsonify({
            "status": "Withdraw successful",
            "amount": str(w3.from_wei(balance_wei, "ether")),
            "tx_hash": tx_hash.hex(),
            "block_number": receipt["blockNumber"]
        })
    except Exception as e:
        print(f"Error in withdrawal: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
