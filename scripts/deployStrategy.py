from pathlib import Path
import sys
import os

from brownie import Strategy, accounts, config, network, project, web3
from eth_utils import is_checksum_address
import click


API_VERSION = config["dependencies"][0].split("@")[-1]
Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault


def get_address(msg: str, default: str = None) -> str:
    val = click.prompt(msg, default=default)

    # Keep asking user for click.prompt until it passes
    while True:

        if is_checksum_address(val):
            return val
        elif addr := web3.ens.address(val):
            click.echo(f"Found ENS '{val}' [{addr}]")
            return addr

        click.echo(
            f"I'm sorry, but '{val}' is not a checksummed address or valid ENS record"
        )
        # NOTE: Only display default once
        val = click.prompt(msg)


def main():
    print(f"You are using the '{network.show_active()}' network")

    vault = Vault.at("0x0000000000000000000000000000000000000000")
    strategy = Strategy.at("0x19d48C96d1A69A1ecf923B52383A67Bc59B2Fcd7")

    print(
        f"""
        Strategy
        name: {strategy.name()}
        address: {strategy}
        --------------
        Vault
        vault name: {vault.name()}
        address: {vault}
        """
    )

    gov = accounts.load(click.prompt("Account", type=click.Choice(accounts.load())))

    print(f"You are using: 'dev' [{gov.address}]")

   
    debt_ratio = 100 # 100%
    minDebtPerHarvest = 0  # Lower limit on debt add
    maxDebtPerHarvest = 100_000_000_000 # Upper limit on debt add
    performance_fee = 0 # Strategist perf fee: 10%
   
    vault.addStrategy(
      strategy,
      debt_ratio,
      minDebtPerHarvest,
      maxDebtPerHarvest,
      performance_fee,
      {"from":gov}
    )

    addHealthCheck(strategy, gov, gov)
    


def addHealthCheck(strategy, gov, deployer):
    healthCheck = "0x72f8ac48eb2a90876b3fa20016d6531319ec7b03"
    strategy.setHealthCheck(healthCheck,{"from":deployer})
    return healthCheck

def deploy(Strategy, deployer, gov ,vault):
    print(f"""vault: {vault}""")

    deployArgs= [
        vault, 
        "0x3052A0F6ab15b4AE1df39962d5DdEFacA86DaB47",# _masterChef
        1, # _masterChefPoolId
        "0x4a364f8c717cAAD9A442737Eb7b8A55cc6cf18D8", # _stargateRouter
        5, # _liquidityPoolId
    ] 	
	

    strategy = Strategy.deploy(*deployArgs, {"from": deployer})

    
    return strategy
    
