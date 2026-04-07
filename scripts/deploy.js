const hre = require("hardhat"); 
async function main() { 
console.log("Deploying Donation contract..."); 
const Donation = await hre.ethers.getContractFactory("Donation"); 
const donation = await Donation.deploy(); 
await donation.waitForDeployment(); 
const address = await donation.getAddress(); 
console.log("Donation contract deployed to:", address); 
console.log("Congratulations! Your first contract is deployed!"); 
} 
main().catch((error) => { 
console.error(error); 
process.exitCode = 1; 
});
