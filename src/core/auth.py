"""
Multi-chain authentication module.
Supports SIWE (Sign-In with Ethereum) and Solana Ed25519 signatures.
"""

import base64
import time
from dataclasses import dataclass
from typing import Optional

import requests
from eth_account import Account
from eth_account.messages import encode_defunct

try:
    from solders.keypair import Keypair
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False


@dataclass
class AuthSession:
    """Authenticated session with JWT token"""
    address: str
    token: str
    chain: str
    expires_at: float
    session: requests.Session


class MultiChainAuth:
    """
    Unified authentication for multiple chains.
    Handles nonce retrieval, message signing, and token management.
    """

    def __init__(self, api_base: str, referer: str = ""):
        self.api_base = api_base
        self.referer = referer
        self._sessions: dict[str, AuthSession] = {}

    def _build_session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update({
            "accept": "*/*",
            "content-type": "application/json",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/148.0.0.0 Safari/537.36"
            ),
        })
        if self.referer:
            s.headers["Referer"] = self.referer
        return s

    def login_evm(self, private_key: str, nonce_endpoint: str, login_endpoint: str) -> AuthSession:
        """
        EVM login flow (SIWE):
        1. POST nonce_endpoint with address -> get nonce + message
        2. Sign message with private key (personal_sign)
        3. POST login_endpoint with address, nonce, signature -> get JWT
        """
        account = Account.from_key(private_key)
        address = account.address.lower()
        session = self._build_session()

        # Step 1: Get nonce
        resp = session.post(
            f"{self.api_base}{nonce_endpoint}",
            json={"address": address},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        nonce = data.get("nonce") or data.get("data", {}).get("nonce", "")
        message = data.get("message") or data.get("data", {}).get("message", "")

        if not message:
            raise RuntimeError(f"No message in nonce response: {data}")

        # Step 2: Sign message
        msg = encode_defunct(text=message)
        signed = account.sign_message(msg)
        signature = "0x" + signed.signature.hex()

        # Step 3: Login
        resp = session.post(
            f"{self.api_base}{login_endpoint}",
            json={"address": address, "nonce": nonce, "signature": signature},
            timeout=30,
        )
        resp.raise_for_status()
        login_data = resp.json()

        token = (
            login_data.get("token")
            or login_data.get("data", {}).get("token", "")
        )
        expires_at = login_data.get("expires_at", time.time() + 86400)

        session.headers["authorization"] = f"Bearer {token}"

        auth_session = AuthSession(
            address=address,
            token=token,
            chain="evm",
            expires_at=expires_at if isinstance(expires_at, float) else time.time() + 86400,
            session=session,
        )
        self._sessions[address] = auth_session
        return auth_session

    def login_solana(self, keypair, nonce_endpoint: str, verify_endpoint: str) -> AuthSession:
        """
        Solana login flow:
        1. POST nonce_endpoint with address -> get nonce + message
        2. Sign message with Ed25519 keypair
        3. POST verify_endpoint with address, nonce, signature (base64) -> get JWT
        """
        if not SOLANA_AVAILABLE:
            raise RuntimeError("solders not installed — pip install solders")

        address = str(keypair.pubkey())
        session = self._build_session()

        # Step 1: Get nonce
        resp = session.post(
            f"{self.api_base}{nonce_endpoint}",
            json={"address": address},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        payload = data.get("data") or data
        nonce = payload.get("nonce", "")
        message = payload.get("message", "")

        if not message:
            raise RuntimeError(f"No message in nonce response: {data}")

        # Step 2: Sign message (Ed25519)
        sig = keypair.sign_message(message.encode("utf-8"))
        sig_b64 = base64.b64encode(bytes(sig)).decode()

        # Step 3: Verify
        resp = session.post(
            f"{self.api_base}{verify_endpoint}",
            json={"address": address, "signature": sig_b64, "nonce": nonce},
            timeout=120,
        )
        resp.raise_for_status()
        verify_data = resp.json()
        payload = verify_data.get("data") or verify_data

        token = (
            payload.get("token")
            or payload.get("accessToken")
            or ""
        )
        expires_at = payload.get("expiresAtMs", time.time() * 1000 + 86400000) / 1000

        session.headers["authorization"] = f"Bearer {token}"

        auth_session = AuthSession(
            address=address,
            token=token,
            chain="solana",
            expires_at=expires_at,
            session=session,
        )
        self._sessions[address] = auth_session
        return auth_session

    def get_session(self, address: str) -> Optional[AuthSession]:
        """Get cached session if still valid"""
        session = self._sessions.get(address.lower())
        if session and session.expires_at > time.time():
            return session
        return None

    def is_expired(self, address: str) -> bool:
        session = self._sessions.get(address.lower())
        if not session:
            return True
        return session.expires_at <= time.time()
