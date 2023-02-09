import pytest
from brownie import config, Contract, chain

import sys
import os

script_dir = os.path.dirname( __file__ )
strategyDeploy_dir = os.path.join( script_dir ,  ".." , "scripts" )
sys.path.append( strategyDeploy_dir )

from deployStrategy import addHealthCheck, deploy

# use this to set what chain we use. 1 for ETH, 250 for fantom
chain_used = 102

@pytest.fixture
def gov(accounts):
    yield accounts[0]

@pytest.fixture
def user(accounts):
    yield accounts[0]

@pytest.fixture
def user2(accounts):
    yield accounts[9]

@pytest.fixture
def user3(accounts):
    yield accounts[7]

@pytest.fixture
def userWithWeth(accounts):
    yield accounts.at("0x57757e3d981446d585af0d9ae4d7df6d64647806", force=True)


@pytest.fixture
def rewards(accounts):
    yield accounts[1]


@pytest.fixture
def guardian(accounts):
    yield accounts[0]


@pytest.fixture
def management(accounts):
    yield accounts[0]


@pytest.fixture
def strategist(accounts):
    yield accounts[4]


@pytest.fixture
def keeper(accounts):
    yield accounts[0]


@pytest.fixture
def token():
    token_address = "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56"  # address of the ERC-20 used by the strategy/vault (Binance-Peg BSC-USD (BSC-USD))
    yield Contract.from_explorer(token_address)

@pytest.fixture
def dai():
    token_address = "0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3"  # this DAI for sweep testing (Binance-Peg Dai Token (DAI))
    yield Contract.from_explorer(token_address)

@pytest.fixture
def userWithDAI(accounts):
    yield accounts.at("0x8894e0a0c962cb723c1976a4421c95949be2d4e3", force=True)

@pytest.fixture
def userWithWeth(accounts):
    yield accounts.at("0x57757e3d981446d585af0d9ae4d7df6d64647806", force=True)
    
@pytest.fixture
def token_whale(accounts):
    token_address = "0x8894e0a0c962cb723c1976a4421c95949be2d4e3"  # this should be the address of the ERC-20 used by the strategy/vault (DAI)
    yield accounts.at(token_address,force=True)

@pytest.fixture
def reward():
    token_address = "0xB0D502E938ed5f4df2E681fE6E419ff29631d62b" # StargateToken (STG)
    yield Contract.from_explorer(token_address)

@pytest.fixture
def reward_whale(accounts):
    token_address = "0x8894e0a0c962cb723c1976a4421c95949be2d4e3"
    return accounts.at(token_address, force=True)


@pytest.fixture
def amount(accounts, token, user):
    amount = 100_000 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at("0x8894e0a0c962cb723c1976a4421c95949be2d4e3", force=True)
    token.transfer(user, amount, {"from": reserve})
    yield amount

@pytest.fixture
def amount2(accounts, token, user2):
    amount = 10_000 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at("0x8894e0a0c962cb723c1976a4421c95949be2d4e3", force=True)
    token.transfer(user2, amount, {"from": reserve})
    yield amount

@pytest.fixture
def amount3(accounts, token, user3):
    amount = 100_000 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at("0x8894e0a0c962cb723c1976a4421c95949be2d4e3", force=True)
    token.transfer(user3, amount, {"from": reserve})
    yield amount


@pytest.fixture
def weth():
    token_address = "0x2170Ed0880ac9A755fd29B2688956BD959F933F8" # Binance-Peg Ethereum Token (ETH)
    yield Contract.from_explorer(token_address)


@pytest.fixture
def weth_amount(user, weth):
    weth_amount = 10 ** weth.decimals()
    user.transfer(weth, weth_amount)
    yield weth_amount


@pytest.fixture
def vault(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian, management)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    vault.setPerformanceFee(0,  {"from": gov})
    vault.setManagementFee(0,  {"from": gov})
    chain.sleep(1)
    yield vault


@pytest.fixture
def strategy(strategist, keeper, vault, Strategy, gov):
    strategy = deployStrategy(Strategy, strategist, gov ,vault)
    # strategy = strategist.deploy(Strategy, vault)
    strategy.setKeeper(keeper)
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    strategy.setDust(1e18, 1e18, {"from": gov})
    # addHealthCheck(strategy, gov, gov)
    # strategy.setHealthCheck(healthCheck, {"from": gov})
    # strategy.setDoHealthCheck(True, {"from": gov})
    chain.sleep(1)
    chain.mine(1)
    yield strategy

def deployStrategy(Strategy, strategist, gov, vault):
    return deploy(Strategy, strategist, gov ,vault)


@pytest.fixture(scope="session")
def RELATIVE_APPROX():
    # this is more permissive due to single sided deposits and pool size which incurs slippage and prize impact
    yield 1e-2 # 0.1% of slippage
    

# Function scoped isolation fixture to enable x dist.
# Snapshots the chain before each test and reverts after test completion.
@pytest.fixture(scope="function", autouse=True)
def shared_setup(fn_isolation):
    pass

# Snapshots the chain before each test and reverts after test completion.
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass