from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from web3 import Web3
import json
import os
from dotenv import load_dotenv

# Load environment variables

load_dotenv()

app = Flask(**name**, static_folder="../frontend")
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
print("⚠️ Failed to connect to Sepolia (app will still run)")

# Get account safely

account = None
if PRIVATE_KEY:
try:
account = w3.eth.account.from_key(PRIVATE_KEY)
print(f"Using account: {account.address}")

```
    balance = w3.eth.get_balance(account.address)  
    balance_eth = w3.from_wei(balance, "ether")  
    print(f"Account balance: {balance_eth} ETH")  
except Exception as e:  
    print(f"Error loading account: {e}")  
```

else:
print("⚠️ PRIVATE_KEY not set")

# Load contract safely

contract = None
try:
with open("../artifacts/contracts/Donation.sol/Donation.json") as f:
contract_json = json.load(f)
abi = contract_json["abi"]

```
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)  
print("Contract loaded successfully")  

if account:  
    owner = contract.functions.owner().call()  
    print(f"Contract owner: {owner}")  
```

except Exception as e:
print(f"⚠️ Contract load failed: {e}")

# -------- ROUTES --------

@app.route("/")
def home():
return jsonify({
"status": "running",
"network": "sepolia",
"account": account.address if account else "not set",
"contract": CONTRACT_ADDRESS
})

@app.route("/frontend")
def serve_frontend():
return send_from_directory(app.static_folder, "index.html")

@app.route("/[path:path](path:path)")
def serve_static(path):
return send_from_directory(app.static_folder, path)

@app.route("/balance", methods=["GET"])
def get_balance():
try:
if not contract:
return jsonify({"error": "Contract not loaded"}), 500

```
    balance_wei = contract.functions.getBalance().call()  
    balance_eth = w3.from_wei(balance_wei, "ether")  

    return jsonify({  
        "balance": str(balance_eth),  
        "balance_wei": str(balance_wei)  
    })  
except Exception as e:  
    return jsonify({"error": str(e)}), 500  
```

@app.route("/donate", methods=["POST"])
def donate():
try:
if not contract or not account:
return jsonify({"error": "Backend not properly configured"}), 500

```
    data = request.get_json()  
    amount = float(data.get("amount", 0))  

    if amount <= 0:  
        return jsonify({"error": "Invalid amount"}), 400  

    amount_wei = w3.to_wei(amount, "ether")  
    nonce = w3.eth.get_transaction_count(account.address)  

    tx = contract.functions.donate().build_transaction({  
        "from": account.address,  
        "value": amount_wei,  
        "nonce": nonce,  
        "gas": 200000,  
        "gasPrice": w3.eth.gas_price  
    })  

    signed_tx = account.sign_transaction(tx)  
    raw_tx = getattr(signed_tx, "raw_transaction", signed_tx.rawTransaction)  

    tx_hash = w3.eth.send_raw_transaction(raw_tx)  
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)  

    return jsonify({  
        "status": "success",  
        "tx_hash": tx_hash.hex(),  
        "block": receipt["blockNumber"]  
    })  

except Exception as e:  
    return jsonify({"error": str(e)}), 500  
```

@app.route("/withdraw", methods=["POST"])
def withdraw():
try:
if not contract or not account:
return jsonify({"error": "Backend not configured"}), 500

```
    owner = contract.functions.owner().call()  
    if account.address.lower() != owner.lower():  
        return jsonify({"error": "Not owner"}), 403  

    nonce = w3.eth.get_transaction_count(account.address)  

    tx = contract.functions.withdraw().build_transaction({  
        "from": account.address,  
        "nonce": nonce,  
        "gas": 100000,  
        "gasPrice": w3.eth.gas_price  
    })  

    signed_tx = account.sign_transaction(tx)  
    raw_tx = getattr(signed_tx, "raw_transaction", signed_tx.rawTransaction)  

    tx_hash = w3.eth.send_raw_transaction(raw_tx)  
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)  

    return jsonify({  
        "status": "withdraw success",  
        "tx_hash": tx_hash.hex()  
    })  

except Exception as e:  
    return jsonify({"error": str(e)}), 500  
```

# -------- RUN APP --------

if **name** == "**main**":
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
