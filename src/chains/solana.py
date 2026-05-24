"""Solana chain interactions"""

import base64

try:
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


class SolanaChain:
    """Solana chain interaction layer"""

    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url

    def generate_keypair(self) -> tuple[str, str]:
        """Generate new Solana keypair. Returns (address, secret_b58)"""
        if not AVAILABLE:
            raise RuntimeError("solders not installed")
        kp = Keypair()
        import base58
        return str(kp.pubkey()), base58.b58encode(bytes(kp)).decode()

    def sign_message(self, keypair: "Keypair", message: str) -> str:
        """Sign message, return base64 signature"""
        sig = keypair.sign_message(message.encode("utf-8"))
        return base64.b64encode(bytes(sig)).decode()
