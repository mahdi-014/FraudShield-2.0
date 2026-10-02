"""Configuration, credentials management, and server-side authorization."""
import os
import json
import secrets
from dataclasses import dataclass
from typing import Optional, Dict

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

ROLE_SERVICE = 'service'
ROLE_ANALYST = 'analyst'
ROLE_LEGACY = 'legacy_scorer'

@dataclass(frozen=True)
class Actor:
    identity: str
    role: str

class AuthConfig:
    def __init__(self):
        self.token_to_actor: Dict[str, Actor] = {}
        self.load_credentials()

    def _parse_key_spec(self, raw: str, default_identity_prefix: str, role: str):
        raw = raw.strip()
        if not raw:
            return
        # Support JSON dict
        if raw.startswith('{'):
            try:
                mapping = json.loads(raw)
                for token, identity in mapping.items():
                    token = str(token).strip()
                    identity = str(identity).strip()
                    self._register_token(token, identity, role)
                return
            except json.JSONDecodeError:
                pass
        # Support comma-separated "token:identity" or just "token"
        parts = [p.strip() for p in raw.split(',') if p.strip()]
        for idx, part in enumerate(parts):
            if ':' in part:
                token, identity = part.split(':', 1)
                token = token.strip()
                identity = identity.strip()
            else:
                token = part.strip()
                identity = f"{default_identity_prefix}_{idx + 1}"
            self._register_token(token, identity, role)

    def _register_token(self, token: str, identity: str, role: str):
        if not identity.strip() or len(identity) > 100:
            raise ValueError('Actor identity must contain 1 to 100 nonblank characters')
        if len(token) < 24:
            raise ValueError(f"Credential for '{identity}' must be at least 24 characters")
        if token in self.token_to_actor:
            existing_actor = self.token_to_actor[token]
            if existing_actor.role != role:
                raise ValueError(
                    f"Duplicate credential detected across roles: '{existing_actor.role}' and '{role}'"
                )
            # Duplicate token within the same role with different identity
            if existing_actor.identity != identity:
                raise ValueError(
                    f"Credential already assigned to identity '{existing_actor.identity}' in role '{role}'"
                )
            return
        self.token_to_actor[token] = Actor(identity=identity, role=role)

    def load_credentials(self):
        self.token_to_actor.clear()

        # Legacy API key (preserved for backwards compatibility with scoring endpoints)
        legacy_key = os.environ.get('FRAUDSHIELD_API_KEY', '').strip()
        if legacy_key:
            self._register_token(legacy_key, 'legacy_scorer', ROLE_LEGACY)

        # Service credentials
        service_keys = os.environ.get('FRAUDSHIELD_SERVICE_KEYS', '').strip()
        if service_keys:
            self._parse_key_spec(service_keys, 'service', ROLE_SERVICE)
        single_service_key = os.environ.get('FRAUDSHIELD_SERVICE_KEY', '').strip()
        if single_service_key:
            self._register_token(single_service_key, 'default_service', ROLE_SERVICE)

        # Analyst credentials
        analyst_keys = os.environ.get('FRAUDSHIELD_ANALYST_KEYS', '').strip()
        if analyst_keys:
            self._parse_key_spec(analyst_keys, 'analyst', ROLE_ANALYST)
        single_analyst_key = os.environ.get('FRAUDSHIELD_ANALYST_KEY', '').strip()
        if single_analyst_key:
            self._register_token(single_analyst_key, 'default_analyst', ROLE_ANALYST)

    def authenticate(self, token: Optional[str]) -> Optional[Actor]:
        if not token:
            return None
        # Constant-time comparison across configured tokens to avoid timing leaks
        matched_actor = None
        for configured_token, actor in self.token_to_actor.items():
            if secrets.compare_digest(token, configured_token):
                matched_actor = actor
        return matched_actor

def get_database_url() -> Optional[str]:
    url = os.environ.get('DATABASE_URL', '').strip()
    return url if url else None

def get_test_database_url() -> Optional[str]:
    url = os.environ.get('TEST_DATABASE_URL', '').strip()
    return url if url else None

def get_artifact_dir() -> str:
    return os.environ.get('FRAUDSHIELD_ARTIFACT_DIR', 'artifacts')
