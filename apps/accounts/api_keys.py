import hashlib
import secrets
from dataclasses import dataclass

from django.core.cache import cache

from apps.accounts.models import APIKey


@dataclass(frozen=True)
class APIKeyAuthResult:
    api_key: APIKey
    raw_key: str


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def create_api_key(user, name: str = "Default Key") -> tuple[APIKey, str]:
    raw = f"llk_{secrets.token_urlsafe(32)}"
    key_hash = _hash_key(raw)
    prefix = raw[:12]
    api_key = APIKey.objects.create(user=user, name=name, prefix=prefix, key_hash=key_hash)
    return api_key, raw


def authenticate_raw_api_key(raw_key: str) -> APIKeyAuthResult | None:
    if not raw_key or not raw_key.startswith("llk_"):
        return None
    key_hash = _hash_key(raw_key)
    api_key = APIKey.objects.filter(key_hash=key_hash, revoked=False).select_related(
        "user", "user__profile"
    ).first()
    if not api_key:
        return None
    return APIKeyAuthResult(api_key=api_key, raw_key=raw_key)


def enforce_api_key_rate_limits(api_key: APIKey, minute_limit: int, day_limit: int) -> bool:
    minute_key = f"api_key_minute:{api_key.id}"
    day_key = f"api_key_day:{api_key.id}"

    minute_count = cache.get(minute_key, 0)
    day_count = cache.get(day_key, 0)
    if minute_count >= minute_limit or day_count >= day_limit:
        return False

    cache.set(minute_key, minute_count + 1, timeout=60)
    cache.set(day_key, day_count + 1, timeout=86400)
    return True
