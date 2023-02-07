from brownie import Contract

def stateOfStrat(msg, strategy, token):
    print(f'\n===={msg}====')
    wantDec = 10 ** token.decimals()
    print(f'Balance of {token.symbol()}: {strategy.balanceOfWant() / wantDec}')
    print(f'Balance of Bpt: {strategy.balanceOfLpTokens() / wantDec}')
    print(f'Estimated Total Assets: {strategy.estimatedTotalAssets() / wantDec}')

# Balancer uses blocks count to give rewards so the Chain.sleep() method of time travel does not work
# Chain.mine() is too slow so the best solution is to airdrop rewards
def airdrop_rewards(strategy, reward, reward_whale):
    reward.approve(strategy, 2 ** 256 - 1, {'from': reward_whale})
    reward.transfer(strategy, 1000  * 1e18 , {'from': reward_whale})