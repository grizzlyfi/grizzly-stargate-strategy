import brownie
import pytest

import util

def test_operation(
    chain, token, vault, strategy, user, amount, RELATIVE_APPROX, gov
):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # harvest
    chain.sleep(1)
    strategy.harvest({"from": gov})
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=1e-3) == amount


    # withdrawal
    vaultShares = vault.balanceOf(user)
    maxLoss = 20 # 0.1% BPS
    vault.withdraw(vaultShares, user, maxLoss,{"from": user})
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == user_balance_before
    )

def test_operation_half(
    chain, token, vault, strategy, user, gov, amount, RELATIVE_APPROX
):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # harvest
    chain.sleep(1)
    strategy.harvest({"from":gov})

    # withdrawal
    vaultShares = vault.balanceOf(user)
    maxLoss = 10 # 0.1% BPS
    vault.withdraw(vaultShares / 2, user, maxLoss,{"from": user})
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == user_balance_before - amount / 2
    )
    assert (
        pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount / 2
    )
    # withdrawal
    vaultShares = vault.balanceOf(user)
    maxLoss = 5 # 0.1% BPS
    vault.withdraw(vaultShares, user, maxLoss,{"from": user})
    assert (
        pytest.approx(token.balanceOf(user), rel=10-4) == user_balance_before
    )


def test_operation_half_withdraw(
    chain, token, vault, strategy, gov,user, amount, RELATIVE_APPROX, reward, reward_whale 
):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Deposit funds on the strategy and invest them
    chain.sleep(1)
    strategy.harvest({"from":gov})
    stratInitialAssets = strategy.estimatedTotalAssets()
    assert pytest.approx(stratInitialAssets, rel=RELATIVE_APPROX) == amount

    util.airdrop_rewards(strategy, reward, reward_whale )

    chain.mine(1)
    strategy.harvest({"from":gov})
    assert vault.totalAssets() > amount

    time= 86400 # 100 days of work = 1/3 years
    util.airdrop_rewards(strategy, reward, reward_whale )
    chain.mine(1)
    strategy.harvest({"from":gov})

    assert strategy.estimatedTotalAssets() > stratInitialAssets

def test_claim_rewards(
    chain, token, vault,gov, strategy, user, amount, RELATIVE_APPROX, reward, reward_whale
):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Deposit funds on the strategy and invest them
    chain.sleep(1)
    strategy.harvest({"from":gov})
    stratInitialAssets = strategy.estimatedTotalAssets()
    assert pytest.approx(stratInitialAssets, rel=RELATIVE_APPROX) == amount

    util.airdrop_rewards(strategy, reward, reward_whale)
    chain.mine(1)
    rewardsBeforeTend = strategy.pendingRewards()
    strategy.tend({"from":gov})
    rewardsAfterTend = strategy.pendingRewards()

    assert rewardsBeforeTend > rewardsAfterTend
    assert rewardsAfterTend < 1e16
    assert strategy.estimatedTotalAssets() > amount

def test_emergency_exit(
    chain, token, vault,gov, strategy, user, amount, RELATIVE_APPROX,
    reward, reward_whale 
):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    chain.sleep(1)
    strategy.harvest({"from":gov})
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    util.airdrop_rewards(strategy, reward, reward_whale)
    chain.mine()
    strategy.harvest()
    # set emergency and exit
    strategy.setEmergencyExit({"from":gov})
    strategy.harvest({"from": gov})

    assert strategy.estimatedTotalAssets() < 1e5

def test_profitable_harvest(
    chain, token, vault,gov, strategy, user, amount, RELATIVE_APPROX, reward, reward_whale 
):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Harvest 1: Send funds through the strategy
    chain.sleep(1)
    strategy.harvest({"from":gov})
    stratInitAssets = strategy.estimatedTotalAssets()
    assert pytest.approx(stratInitAssets, rel=1e-3) == amount

    before_pps = vault.pricePerShare()

    # Harvest 2: Realize profit
    time= 86400 # 1 days of work
    util.airdrop_rewards(strategy, reward, reward_whale )
    chain.sleep(3600 * 6)
    chain.mine(1)

    strategy.harvest({"from":gov})
    # Check that all rewards have been sold
    assert strategy.balanceOfReward() == 0
    
    # 6 hrs needed for profits to unlock on the vault
    chain.sleep(3600 * 6)
    chain.mine(10)

    assert vault.pricePerShare() > before_pps
    assert vault.totalAssets() > amount

    strategy.harvest({"from":gov})
    assert strategy.estimatedTotalAssets() > stratInitAssets

# Passing but dangerous maxLoss
def test_deposit_withdraw(
    chain, token, vault,gov, strategy, user, amount, RELATIVE_APPROX
):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # harvest
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from":gov})
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # tend()
    strategy.tend({"from":gov})

    # withdrawal
    vaultShares = vault.balanceOf(user)
    maxLoss = 20 # 0.15% BPS
    vault.withdraw(vaultShares, user, maxLoss,{"from": user})
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == user_balance_before
    )

def test_profitability_of_strategy(
    chain, token, vault,gov, strategy, user, amount, RELATIVE_APPROX, reward, reward_whale 
):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Harvest 1: Send funds through the strategy
    chain.sleep(1)
    strategy.harvest({"from":gov})
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # Harvest 2: Realize profit
    time = 86400 * 1 # 1 day of running the strategy
    util.airdrop_rewards(strategy, reward, reward_whale )
    chain.sleep(1800)
    chain.mine(1)
    strategy.harvest({"from":gov})

    chain.sleep(3600 * 6)
    chain.mine(1)

    assert vault.totalAssets() > amount

    print(f"""vault.totalAssets(): {vault.totalAssets()}""" )
    print(f"""ETA: {strategy.estimatedTotalAssets()}""" )

    # Withdrawal
    vaultShares = vault.balanceOf(user)
    maxLoss = 10 # 0.10% BPS
    vault.withdraw(vaultShares, user, maxLoss,{"from": user})
    assert token.balanceOf(user) > user_balance_before
    

def test_change_debt(
    chain, gov, token,vault, strategy, user, amount, RELATIVE_APPROX
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from":gov})
    half = int(amount / 2)

    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half

    vault.updateStrategyDebtRatio(strategy.address, 10_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from":gov})
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from":gov})
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half

def test_sweep(gov, vault, strategy, token, user, userWithDAI, RELATIVE_APPROX, amount, dai):
    # Strategy want token doesn't work
    token.transfer(strategy, amount, {"from": user})
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0
    with brownie.reverts("!want"):
        strategy.sweep(token, {"from": gov})

    # Vault share token doesn't work
    with brownie.reverts("!shares"):
        strategy.sweep(vault.address, {"from": gov})

    # Protected token doesn't work
    # with brownie.reverts("!protected"):
    #     strategy.sweep(strategy.protectedToken(), {"from": gov})

    before_balance = dai.balanceOf(gov)
    transferAmount = 1000 * 1e18
    dai.transfer(strategy, transferAmount, {"from": userWithDAI})
    assert dai.address != strategy.want()
    assert dai.balanceOf(user) < 1e18 # There is 0,14 DAI in accounts[0] 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
    strategy.sweep(dai, {"from": gov})
    sumBal = transferAmount + before_balance
    assert pytest.approx(dai.balanceOf(gov), rel=RELATIVE_APPROX) == sumBal

def test_autocompounding(chain, vault, strategy, token,gov, amount, user, RELATIVE_APPROX,  reward, reward_whale ):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Harvest 1: Send funds to the strategy
    chain.sleep(1)
    strategy.harvest({"from":gov})
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # Tend 1: Re-invest rewards    
    stratPrevTendAssets =  strategy.estimatedTotalAssets()
    for x in range(7):
        util.airdrop_rewards(strategy, reward, reward_whale )
        chain.sleep(3600)
        chain.mine(1)

        strategy.tend({"from":gov})
        currentStratAssets = strategy.estimatedTotalAssets()
        assert stratPrevTendAssets < currentStratAssets
        stratPrevTendAssets = currentStratAssets

    print(f"""TA: {vault.totalAssets()} """)
    print(f"""ETA: {strategy.estimatedTotalAssets()} """)

    chain.sleep(3600)
    chain.mine()
    strategy.setCollectFeesEnabled(True, {"from":gov})
    strategy.harvest({"from":gov})
    chain.sleep(3600 * 6) # wait for the funds to unlock
    chain.mine(1)

    print(f"""TA: {vault.totalAssets()} """)
    print(f"""ETA: {strategy.estimatedTotalAssets()} """)

    vaultShares = vault.balanceOf(user)
    vaultPrice = vault.pricePerShare() / 10**vault.decimals()

    maxLoss = 10 # 0.1% BPS
    vault.withdraw(vaultShares, user, maxLoss,{"from": user})

    userProfit = token.balanceOf(user) - user_balance_before
    userExpectedProfit = vaultPrice * vaultShares - amount
    assert userProfit > 1e8

def test_multiple_harvests(chain, gov,vault, strategy, token, amount, user, RELATIVE_APPROX, reward, reward_whale ):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Harvest 1: Send funds to the strategy
    chain.sleep(1)
    strategy.harvest({"from":gov})

    stratInitialAssets = strategy.estimatedTotalAssets()

    assert pytest.approx(stratInitialAssets, rel=RELATIVE_APPROX) == amount

    # Harvest 2-7: 
    vaultAssets =  0
    for x in range(10):
        time = 86400 * 10 # 1 day of running the strategy
        util.airdrop_rewards(strategy, reward, reward_whale )
        chain.mine(1)
        strategy.harvest({"from":gov})

        chain.sleep(3600 * 6) # Wait for the funds to unlock
        chain.mine(1)
        currentVaultAssets = vault.totalAssets()

        print(f"""day {x} assets: {currentVaultAssets}""")
        assert currentVaultAssets > vaultAssets
        vaultAssets = currentVaultAssets

    assert (strategy.estimatedTotalAssets() - stratInitialAssets ) / stratInitialAssets * 100 * 12 > 1

    userVaultShares = vault.balanceOf(user)
    vaultPrice = vault.pricePerShare() / 10 ** vault.decimals()

    maxLoss = 10 # 0.1% BPS
    vault.withdraw(userVaultShares, user, maxLoss,{"from": user})

    userProfit = token.balanceOf(user) - user_balance_before
    userExpectedProfit = vaultPrice * userVaultShares
    withdrawLoss = (userExpectedProfit - token.balanceOf(user)) / token.balanceOf(user) 
    assert withdrawLoss < 0.1
    assert pytest.approx(userProfit, rel=10e-2) == userExpectedProfit - amount

    dailyAPR = 10/365 * 0.8
    compoundingFormula = stratInitialAssets * ((1 + (dailyAPR/30)) ** 30 - 1)

    assert userProfit >= compoundingFormula - amount

def test_correct_APR(chain,gov, vault, strategy, token, amount, user,  reward, reward_whale ):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Harvest 1: Send funds to the strategy
    chain.sleep(1)
    strategy.harvest({"from":gov})

    stratInitialAssets = strategy.estimatedTotalAssets()

    # Harvest 2-7: 
    # for x in range(30):
    time = 86400 * 30 # 1 day of running the strategy
    util.airdrop_rewards(strategy, reward, reward_whale )
    chain.sleep(3600)
    chain.mine(1)
    strategy.harvest({"from":gov})
    strategy.harvest({"from":gov})
    assert (strategy.estimatedTotalAssets() - stratInitialAssets ) / stratInitialAssets * 100 * 365 > 10

def test_correct_APR_day(chain,gov, vault, strategy, token, amount, user, reward, reward_whale ):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount
    
    # Harvest 1: Send funds to the strategy
    chain.sleep(1)
    strategy.harvest({"from":gov})
    print(f""" vaultAssets: {strategy.estimatedTotalAssets()}""")

    # Harvest 2-7: 
    time = 86400 * 10 # 1 day of running the strategy
    util.airdrop_rewards(strategy, reward, reward_whale )
    chain.sleep(3600 * 6)
    chain.mine(1)
    strategy.harvest({"from":gov})

    chain.sleep(3600 * 6) # Wait for the funds to unlock
    chain.mine(1)
    currentVaultAssets = vault.totalAssets()

    print(f"""currentVaultAssets: {currentVaultAssets}""")

    print(f""" vaultAssets: {vault.totalAssets()}""")

    vaultShares = vault.balanceOf(user)

    maxLoss = 10 # 0.1% BPS
    vault.withdraw(vaultShares, user, maxLoss,{"from": user})

    userProfit = (token.balanceOf(user) - user_balance_before) / user_balance_before * 100 * 365
    assert userProfit > 10


def test_triggers(
    chain, gov, vault, strategy, token, amount, user
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from":gov})

    strategy.harvestTrigger(0)
    strategy.tendTrigger(0)
