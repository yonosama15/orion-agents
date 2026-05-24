"""EVM chain interactions — 0G Chain, Ethereum L2s"""

from web3 import Web3


class EVMChain:
    """EVM-compatible chain interaction layer"""

    RPC_ENDPOINTS = {
        "0g": ["https://evmrpc.0g.ai", "https://0g-evmrpc.stakeme.pro"],
        "ethereum": ["https://eth.llamarpc.com"],
        "base": ["https://mainnet.base.org"],
    }

    def __init__(self, chain: str = "0g"):
        self.chain = chain
        self.w3 = self._connect()

    def _connect(self) -> Web3:
        for rpc in self.RPC_ENDPOINTS.get(self.chain, []):
            try:
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
                if w3.is_connected():
                    return w3
            except Exception:
                continue
        raise ConnectionError(f"Failed to connect to {self.chain}")

    def get_balance(self, address: str) -> float:
        return self.w3.from_wei(self.w3.eth.get_balance(address), "ether")

    def send_transaction(self, signed_tx) -> str:
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt.status != 1:
            raise RuntimeError(f"TX reverted: {tx_hash.hex()}")
        return tx_hash.hex()
