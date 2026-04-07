const { expect } = require("chai");

describe("Donation Contract", function () {
  let donation;
  let owner;
  let addr1;
  let addr2;

  // This runs before each test – gives us a fresh contract
  beforeEach(async function () {
    // Get the contract factory and signers
    const Donation = await ethers.getContractFactory("Donation");
    [owner, addr1, addr2] = await ethers.getSigners();

    // Deploy a new contract for each test
    donation = await Donation.deploy();
    await donation.waitForDeployment(); // v6 method
  });

  // Test 1: Check owner is set correctly
  it("Should set the right owner", async function () {
    expect(await donation.owner()).to.equal(owner.address);
  });

  // Test 2: Contract should accept donations
  it("Should accept donations", async function () {
    // addr1 donates 1 ETH
    await donation.connect(addr1).donate({
      value: ethers.parseEther("1"),
    });

    // Check contract balance
    expect(await donation.getBalance()).to.equal(
      ethers.parseEther("1")
    );
  });

  // Test 3: Total donations counter should update
  it("Should track total donations", async function () {
    await donation.connect(addr1).donate({
      value: ethers.parseEther("1"),
    });

    expect(await donation.totalDonations()).to.equal(
      ethers.parseEther("1")
    );
  });

  // Test 4: Donor mapping should track individual donations
  it("Should track donor mapping", async function () {
    await donation.connect(addr1).donate({
      value: ethers.parseEther("1"),
    });

    expect(
      await donation.donations(addr1.address)
    ).to.equal(ethers.parseEther("1"));
  });

  // Test 5: Multiple donations from same donor should accumulate
  it("Should accumulate multiple donations from same donor", async function () {
    await donation.connect(addr1).donate({
      value: ethers.parseEther("1"),
    });

    await donation.connect(addr1).donate({
      value: ethers.parseEther("2"),
    });

    expect(
      await donation.donations(addr1.address)
    ).to.equal(ethers.parseEther("3"));

    expect(await donation.totalDonations()).to.equal(
      ethers.parseEther("3")
    );
  });

  // Test 6: Owner should be able to withdraw
  it("Should allow owner to withdraw", async function () {
    await donation.connect(addr1).donate({
      value: ethers.parseEther("1"),
    });

    await donation.withdraw();

    expect(await donation.getBalance()).to.equal(0);
  });

  // Test 7: Non-owner should NOT be able to withdraw
  it("Should not allow non-owner to withdraw", async function () {
    await donation.connect(addr1).donate({
      value: ethers.parseEther("1"),
    });

    await expect(
      donation.connect(addr1).withdraw()
    ).to.be.revertedWith("Not owner");
  });

  // Test 8: Check events are emitted correctly
  it("Should emit DonationReceived event", async function () {
    await expect(
      donation
        .connect(addr1)
        .donate({ value: ethers.parseEther("1") })
    )
      .to.emit(donation, "DonationReceived")
      .withArgs(addr1.address, ethers.parseEther("1"));
  });

  // Test 9: Check FundsWithdrawn event
  it("Should emit FundsWithdrawn event", async function () {
    await donation.connect(addr1).donate({
      value: ethers.parseEther("1"),
    });

    await expect(donation.withdraw())
      .to.emit(donation, "FundsWithdrawn")
      .withArgs(owner.address, ethers.parseEther("1"));
  });

  // Test 10: Donation with 0 ETH should fail
  it("Should reject 0 ETH donations", async function () {
    await expect(
      donation.connect(addr1).donate({ value: 0 })
    ).to.be.revertedWith("Donation must be greater than 0");
  });
});
