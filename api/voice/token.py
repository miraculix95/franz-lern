"""HMAC-signiertes Kurzzeit-Token für den Voice-Callback.

Gegenstück zu `signVoiceToken` in lingua-v2 (`src/lib/voice/token.ts`). lingua-v2 mintet das
Token beim Call-Start (User bereits authentifiziert + premium-gated) und reicht es über Vapi
`variableValues` an den custom-llm-Callback in lingua-core. Der Callback verifiziert es hier —
das ist die einzige User-Identität, die der ansonsten stateless core kennt.

Format: base64url(json_claims) + "." + base64url(hmac_sha256(secret, body_b64)).
Claims: {"uid": "<supabase-uuid>", "sid": "<voice-session-uuid>", "exp": <unix>, "plan": "premium"}.
"""
import base64
import hashlib
import hmac
import json
import time


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def verify_voice_token(raw: str, secret: str, now: int | None = None) -> dict | None:
    """Verify a v2-minted voice token. Returns claims dict or None (invalid/expired)."""
    if not raw or not secret or "." not in raw:
        return None
    body_b64, sig_b64 = raw.split(".", 1)
    try:
        expected = hmac.new(secret.encode(), body_b64.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64d(sig_b64)):
            return None
        claims = json.loads(_b64d(body_b64))
    except Exception:
        return None
    now = int(time.time()) if now is None else now
    if int(claims.get("exp", 0)) < now:
        return None
    if not claims.get("uid") or not claims.get("sid"):
        return None
    return claims
