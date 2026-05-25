"""
Add LLM_BACKEND knob to .env.example and .env if missing.
"""
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")

ADDITIONS = (
    "\n# --- LLM backend ---\n"
    "# stub | genlayer\n"
    "LLM_BACKEND=stub\n"
)

for rel in [".env.example", ".env"]:
    p = ROOT / rel
    if not p.exists():
        print(f"  skip  {rel} (not found)")
        continue
    text = p.read_text(encoding="utf-8")
    if "LLM_BACKEND" in text:
        print(f"  skip  {rel} (LLM_BACKEND already present)")
        continue
    p.write_text(text.rstrip() + "\n" + ADDITIONS, encoding="utf-8")
    print(f"  patched {rel}")
