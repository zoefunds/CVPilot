"""
Phase 11A backend: extend JWT access token TTL from 30 minutes to 12 hours
(720 minutes) by default. Override via JWT_ACCESS_TOKEN_EXPIRES_MIN in .env.
"""
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")

# 1) config.py: change default
CONFIG = ROOT / "backend/app/core/config.py"
text = CONFIG.read_text(encoding="utf-8")
OLD = 'jwt_access_token_expires_min: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRES_MIN")'
NEW = 'jwt_access_token_expires_min: int = Field(default=720, alias="JWT_ACCESS_TOKEN_EXPIRES_MIN")'
if OLD in text:
    CONFIG.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print(f"  patched {CONFIG.relative_to(ROOT)} (jwt TTL default = 720 minutes)")
else:
    print(f"  skipped {CONFIG.relative_to(ROOT)} (default already updated)")

# 2) .env.example: surface new default explicitly
ENV_EXAMPLE = ROOT / ".env.example"
text = ENV_EXAMPLE.read_text(encoding="utf-8")
if "JWT_ACCESS_TOKEN_EXPIRES_MIN=720" not in text:
    text = text.replace(
        "JWT_ACCESS_TOKEN_EXPIRES_MIN=30",
        "JWT_ACCESS_TOKEN_EXPIRES_MIN=720",
    )
    ENV_EXAMPLE.write_text(text, encoding="utf-8")
    print(f"  patched {ENV_EXAMPLE.relative_to(ROOT)} (JWT_ACCESS_TOKEN_EXPIRES_MIN=720)")

# 3) Live .env update (best effort)
ENV = ROOT / ".env"
if ENV.exists():
    text = ENV.read_text(encoding="utf-8")
    lines = text.splitlines()
    out, seen = [], False
    for ln in lines:
        if ln.startswith("JWT_ACCESS_TOKEN_EXPIRES_MIN="):
            out.append("JWT_ACCESS_TOKEN_EXPIRES_MIN=720")
            seen = True
        else:
            out.append(ln)
    if not seen:
        out.append("JWT_ACCESS_TOKEN_EXPIRES_MIN=720")
    ENV.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"  patched {ENV.relative_to(ROOT)} (JWT_ACCESS_TOKEN_EXPIRES_MIN=720)")

print("\nPhase 11A backend complete.")
