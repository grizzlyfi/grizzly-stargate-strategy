import pytest

import util

def test_trading_fees(chain, vault, gov ,strategy, token, amount, user, RELATIVE_APPROX, reward, reward_whale):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Harvest 1: Send funds to the strategy
    chain.sleep(1)
    strategy.harvest({"from":gov})
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount
    
    days = 100 # 50 days to recoup the slippage with trading fees
    util.airdrop_rewards(strategy, reward, reward_whale)

    chain.mine(1)
    chain.sleep(3600 * 7) # 1 day of running the strategy
    chain.mine(1)

    strategy.harvest({"from":gov})

    chain.sleep(3600 * 6) # wait for the funds to unlock
    chain.mine(1)

    assert vault.totalAssets() > amount
    # Withdraw user funds
    vault.withdraw({"from": user})
    profits = token.balanceOf(user) - user_balance_before
    assert profits > 1e6
