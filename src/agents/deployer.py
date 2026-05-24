"""
Agent deployment module.
Handles wallet generation, gas funding, on-chain registration, and agent creation.
"""

import secrets
import time
import random
import threading
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from eth_account import Account
from web3 import Web3

Account.enable_unaudited_hdwallet_features()


@dataclass
class DeploymentResult:
    """Result of a single agent deployment"""
    address: str
    private_key: str
    agent_id: Optional[int]
    identity_id: Optional[int]
    tx_hash: Optional[str]
    status: str  # "success", "gas_failed", "login_failed", "agent_failed", "onchain_failed"
    error: str = ""


class AgentDeployer:
    """
    Deploys prediction agents at scale.
    
    Pipeline per agent:
    1. Generate EVM/Solana wallet
    2. Fund with gas from treasury
    3. Authenticate via API (SIWE or Ed25519)
    4. Create agent with domain config
    5. On-chain identity registration
    6. Bind agent to on-chain identity
    """

    # Agent name components for random generation
    PREFIXES = ["Alpha", "Neo", "Sigma", "Delta", "Omega", "Zeta", "Theta", "Kappa", "Lambda", "Phi"]
    SUFFIXES = ["Vision", "Oracle", "Trader", "Predict", "Sight", "Analyst", "Forge", "Signal", "Edge", "Hunter"]

    # Domain-specific prompt templates
    DOMAIN_PROMPTS = {
        "crypto": {
            "focus": "cryptocurrency markets, DeFi protocols, and blockchain ecosystem events",
            "evidence_types": ["on-chain data", "market sentiment", "protocol metrics", "regulatory signals"],
            "style": "data-driven with emphasis on verifiable on-chain evidence",
        },
        "sports": {
            "focus": "professional sports outcomes, player performance, and team dynamics",
            "evidence_types": ["historical stats", "injury reports", "head-to-head records", "venue factors"],
            "style": "statistical with consideration for intangible momentum factors",
        },
        "macro": {
            "focus": "macroeconomic events, central bank decisions, and geopolitical developments",
            "evidence_types": ["economic indicators", "policy statements", "historical precedents", "expert consensus"],
            "style": "conservative with strong emphasis on base rates and historical patterns",
        },
        "events": {
            "focus": "real-world events, technology releases, and cultural milestones",
            "evidence_types": ["official announcements", "insider signals", "timeline analysis", "precedent events"],
            "style": "balanced between optimistic and skeptical interpretations",
        },
    }

    def __init__(self, chain: str = "0g", domain: str = "crypto", gas_per_agent: float = 0.003):
        self.chain = chain
        self.domain = domain
        self.gas_per_agent = gas_per_agent
        self.results_file = Path("deployment_results.txt")
        self._lock = threading.Lock()

    def generate_wallet(self) -> tuple[str, str]:
        """Generate new EVM wallet"""
        acct = Account.create(secrets.token_bytes(32))
        pk = acct.key.hex()
        if not pk.startswith("0x"):
            pk = "0x" + pk
        return acct.address, pk

    def generate_agent_name(self) -> str:
        """Generate random agent name"""
        prefix = random.choice(self.PREFIXES)
        suffix = random.choice(self.SUFFIXES)
        uid = secrets.token_hex(3)
        return f"{prefix}{suffix}_{uid}"

    def get_domain_config(self, domain: str) -> dict:
        """Get domain-specific configuration"""
        return self.DOMAIN_PROMPTS.get(domain, self.DOMAIN_PROMPTS["crypto"])

    def fund_wallet(self, w3: Web3, funder_pk: str, target: str, amount: float) -> str:
        """Send gas to new wallet from treasury"""
        funder = Account.from_key(funder_pk)
        nonce = w3.eth.get_transaction_count(funder.address)

        tx = {
            "from": funder.address,
            "to": Web3.to_checksum_address(target),
            "value": w3.to_wei(amount, "ether"),
            "gas": 21000,
            "gasPrice": w3.eth.gas_price,
            "nonce": nonce,
            "chainId": w3.eth.chain_id,
        }

        signed = w3.eth.account.sign_transaction(tx, funder_pk)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)

        if receipt.status != 1:
            raise RuntimeError(f"Funding TX failed: {tx_hash.hex()}")

        return tx_hash.hex()

    def deploy_single(self, w3: Web3, funder_pk: str, api_client, ref_code: str = "") -> DeploymentResult:
        """Deploy a single agent end-to-end"""
        address, pk = self.generate_wallet()

        try:
            # Fund
            self.fund_wallet(w3, funder_pk, address, self.gas_per_agent)
        except Exception as e:
            return DeploymentResult(address=address, private_key=pk, agent_id=None,
                                   identity_id=None, tx_hash=None, status="gas_failed", error=str(e))

        time.sleep(2)

        try:
            # Login
            api_client.login(pk)
        except Exception as e:
            return DeploymentResult(address=address, private_key=pk, agent_id=None,
                                   identity_id=None, tx_hash=None, status="login_failed", error=str(e))

        try:
            # Redeem invite (optional)
            if ref_code:
                api_client.redeem_invite(ref_code)
        except Exception:
            pass  # Non-critical

        time.sleep(1)

        try:
            # Create agent
            name = self.generate_agent_name()
            domain_config = self.get_domain_config(self.domain)
            agent = api_client.create_agent(name, self.domain, domain_config)
            agent_id = agent.get("id") or agent.get("agent_id")
        except Exception as e:
            return DeploymentResult(address=address, private_key=pk, agent_id=None,
                                   identity_id=None, tx_hash=None, status="agent_failed", error=str(e))

        time.sleep(2)

        try:
            # On-chain registration
            tx_hash, identity_id = api_client.register_onchain(w3, pk, agent_id, name)
        except Exception as e:
            return DeploymentResult(address=address, private_key=pk, agent_id=agent_id,
                                   identity_id=None, tx_hash=None, status="onchain_failed", error=str(e))

        return DeploymentResult(
            address=address, private_key=pk, agent_id=agent_id,
            identity_id=identity_id, tx_hash=tx_hash, status="success"
        )

    def deploy_batch(self, count: int, referral_code: str = "", parallel: int = 1) -> list[DeploymentResult]:
        """Deploy multiple agents with optional parallelism"""
        results = []

        # Sequential for now (on-chain nonce management)
        for i in range(count):
            print(f"  [{i+1}/{count}] Deploying...")
            # result = self.deploy_single(...)
            # results.append(result)
            time.sleep(random.uniform(3, 8))

        return results

    def _save_result(self, result: DeploymentResult):
        """Persist deployment result"""
        with self._lock, self.results_file.open("a", encoding="utf-8") as f:
            f.write(f"{result.address} | {result.private_key} | {result.status} | "
                    f"agent={result.agent_id} identity={result.identity_id} tx={result.tx_hash}\n")
