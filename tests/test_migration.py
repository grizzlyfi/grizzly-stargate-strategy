import pytest
from conftest import deployStrategy
import util

def test_funds_migration(
    chain,
    token,
    vault,
    strategy,
    amount,
    Strategy,
    strategist,
    gov,
    user,
    RELATIVE_APPROX,
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    chain.sleep(1)
    strategy.harvest({"from":gov})

    estimatedTotalAssets = strategy.estimatedTotalAssets()
    assert pytest.approx(estimatedTotalAssets, rel=RELATIVE_APPROX) == amount

    rewards = strategy.balanceOfReward()
    print(f'balanceOfRewards before: {rewards / 10 ** 18}')

    balanceOfLPTokens = strategy.balanceOfLpTokens() + strategy.balanceOfLPInMasterChef()
    print(f'balanceOfLPTokens before: {balanceOfLPTokens / 10 ** token.decimals()}')

    # Deploy new strategy
    new_strategy = deployStrategy(Strategy, strategist, gov, vault)
    # Migrate to a new strategy

    # Harvest new strategy to re-invest everything
    strategy.harvest({"from":gov})
    vault.migrateStrategy(strategy, new_strategy, {"from": gov})
    new_strategy.harvest({"from":gov})
    # assert that the old strategy does not have any funds
    assert strategy.estimatedTotalAssets() == 0
    assert strategy.balanceOfLpTokens() == 0
    assert strategy.balanceOfLPInMasterChef() == 0

    # assert that all the funds ( want, LP and rewards) have been migrated correctly
    assert  pytest.approx(new_strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)== estimatedTotalAssets
    totalLpTokens = new_strategy.balanceOfLpTokens() +  new_strategy.balanceOfLPInMasterChef()
    print(f'balanceOfLPTokens after: {totalLpTokens / 10 ** token.decimals()}')
    assert  pytest.approx(totalLpTokens, rel=RELATIVE_APPROX) == balanceOfLPTokens
    print(f'balanceOfRewards after: {new_strategy.balanceOfReward() / 10 ** 18}')
    diffRewards = new_strategy.balanceOfReward() - rewards
    assert diffRewards < 1e18


def test_funds_migration_abandonRewards(
    chain,
    token,
    vault,
    strategy,
    amount,
    Strategy,
    strategist,
    gov,
    user,
    RELATIVE_APPROX,
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    chain.sleep(1)
    strategy.harvest({"from":gov})

    estimatedTotalAssets = strategy.estimatedTotalAssets()
    assert pytest.approx(estimatedTotalAssets, rel=RELATIVE_APPROX) == amount

    rewards = strategy.balanceOfReward()
    print(f'balanceOfRewards before: {rewards / 10 ** 18}')

    balanceOfLPTokens = strategy.balanceOfLpTokens() + strategy.balanceOfLPInMasterChef()
    print(f'balanceOfLPTokens before: {balanceOfLPTokens / 10 ** token.decimals()}')

    # Deploy new strategy
    new_strategy = deployStrategy(Strategy, strategist, gov, vault)
    # Migrate to a new strategy

    # Harvest new strategy to re-invest everything
    # strategy.harvest({"from":gov})
    strategy.setAbandonRewards(True, {"from": gov})
    vault.migrateStrategy(strategy, new_strategy, {"from": gov})
    chain.mine(1)
    chain.sleep(3600 * 7) # 1 day of running the strategy
    chain.mine(1)
    new_strategy.harvest({"from":gov})
    # assert that the old strategy does not have any funds
    assert strategy.estimatedTotalAssets() == 0
    assert strategy.balanceOfLpTokens() == 0
    assert strategy.balanceOfLPInMasterChef() == 0

    # assert that all the funds ( want, LP and rewards) have been migrated correctly
    assert  pytest.approx(new_strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)== estimatedTotalAssets
    totalLpTokens = new_strategy.balanceOfLpTokens() +  new_strategy.balanceOfLPInMasterChef()
    print(f'balanceOfLPTokens after: {totalLpTokens / 10 ** token.decimals()}')
    assert  pytest.approx(totalLpTokens, rel=RELATIVE_APPROX) == balanceOfLPTokens
    print(f'balanceOfRewards after: {new_strategy.balanceOfReward() / 10 ** 18}')
    assert  pytest.approx(new_strategy.balanceOfReward(), rel=RELATIVE_APPROX) == rewards # Some small rewards are generated with chain time


def test_migration(
    chain,
    token,
    vault,
    strategy,
    amount,
    Strategy,
    strategist,
    gov,
    user,
    RELATIVE_APPROX,
    reward, reward_whale
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    #Deposit Funds on the strategy
    strategy.harvest({"from":gov})
    stratInitialAssets = strategy.estimatedTotalAssets()
    pricePerShare = vault.pricePerShare()

    assert pytest.approx(stratInitialAssets, rel=RELATIVE_APPROX) == amount

    # Deploy new strategy
    new_strategy = deployStrategy(Strategy, strategist, gov, vault)
    new_strategy.setKeeper(gov)

    assert (strategy.address != new_strategy.address)
    # Migrate to a new strategy
    vault.migrateStrategy(strategy, new_strategy, {"from": gov})
    vaultTotalAssets = vault.totalAssets()

    newStratEstimatedAssets = new_strategy.estimatedTotalAssets()

    assert vault.totalAssets() >= amount
    assert strategy.estimatedTotalAssets() == 0

    # Run strategy to make sure we are still earning money
    util.airdrop_rewards(new_strategy, reward, reward_whale)
    chain.mine(1)
    new_strategy.setDust(1e18, 1e18, {"from": gov})
    new_strategy.harvest({"from": gov})

    assert new_strategy.estimatedTotalAssets() >  newStratEstimatedAssets or vault.totalAssets() > vaultTotalAssets

    chain.mine(1)
    chain.sleep(3600*6)
    chain.mine(1)
    new_strategy.harvest({"from":gov})

    assert vault.totalAssets() > amount
    assert vault.pricePerShare() > pricePerShare
