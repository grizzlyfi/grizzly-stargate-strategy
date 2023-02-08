# TODO: Add tests that show proper operation of this strategy through "emergencyExit"
#       Make sure to demonstrate the "worst case losses" as well as the time it takes

from brownie import ZERO_ADDRESS
import util
import pytest

def test_vault_shutdown_can_withdraw(
    chain, token, vault,gov, strategy, user, amount, RELATIVE_APPROX
):
    ## Deposit in Vault
    userBalance = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # if token.balanceOf(user) > 0:
    #     token.transfer(ZERO_ADDRESS, token.balanceOf(user), {"from": user})

    # Harvest 1: Send funds through the strategy
    strategy.harvest({"from":gov})
    chain.sleep(3600 * 7)
    chain.mine(1)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    ## Set Emergency
    vault.setEmergencyShutdown(True,{"from":gov})

    ## Withdraw (does it work, do you get what you expect)
    userVaultShares = vault.balanceOf(user)
    maxLoss = 20 # 0.05% BPS
    vault.withdraw(userVaultShares, user, maxLoss,{"from": user})

    assert pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == userBalance


def test_basic_shutdown(
    chain, token, vault, gov,strategy, user, strategist, amount, RELATIVE_APPROX,
    reward, reward_whale
):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Harvest 1: Send funds through the strategy
    strategy.harvest({"from":gov})
    chain.mine(1)

    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # Earn interest
    util.airdrop_rewards(strategy, reward, reward_whale)
    chain.mine(1)
    chain.sleep(3600 * 7) # 1 day of running the strategy
    chain.mine(1)
    
    # Harvest 2: Realize profit
    strategy.harvest({"from":gov})

    # Unlock Profits on the vault
    chain.sleep(3600 * 6) 
    chain.mine(1)

    # Set emergency
    strategy.setEmergencyExit({"from": gov})
    # Remove funds from strategy
    strategy.harvest({"from":gov})  

    assert vault.strategies(strategy).dict()["totalDebt"] == 0
    # Get strategist Fees
    print(f""" token: {token} """)

    # It may not be 0 since we after doing a reinvest of rewards on the adjust position which
    # is run after we have sent the want token to the vault. 
    # This number should be close to 0
    assert pytest.approx(token.balanceOf(strategy), rel=10-2) == 0
    assert vault.totalAssets() > amount # The vault has all the funds

