pragma solidity ^0.8.24; 
contract Donation { 
// State variables 
address public owner; 
uint public totalDonations; 
mapping(address => uint) public donations; 
 // Events 
    event DonationReceived(address indexed donor, uint amount); 
    event FundsWithdrawn(address indexed owner, uint amount); 
 
    // Constructor – runs once when contract is deployed 
    constructor() { 
        owner = msg.sender; 
    } 
 
    // Donate function – receives ETH and tracks donor 
    function donate() public payable { 
        require(msg.value > 0, "Donation must be greater than 0"); 
 
        // Update donor's total 
        donations[msg.sender] += msg.value; 
        // Update overall total 
        totalDonations += msg.value; 
 
        // Emit event for frontend to detect 
        emit DonationReceived(msg.sender, msg.value); 
    } 
 
    // Check contract balance 
    function getBalance() public view returns(uint) { 
        return address(this).balance; 
    }
 // Withdraw function – only owner can call 
    function withdraw() public { 
        // Check that caller is the owner 
        require(msg.sender == owner, "Not owner"); 
 
        // Get current balance 
        uint balance = address(this).balance; 
        require(balance > 0, "No funds to withdraw"); 
 
        // Transfer funds to owner 
        payable(owner).transfer(balance); 
 
        // Emit withdrawal event 
        emit FundsWithdrawn(owner, balance); 
    } 
}
