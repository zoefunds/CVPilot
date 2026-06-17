"""
Set GENLAYER_CONTRACT_ADDRESS in .env to the deployed address.
Leave LLM_BACKEND=stub for now; the user flips it manually for the smoke test.
"""
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
ADDR = "0xDb65251DDB51Fcb20dfA9bbaE17D80efa4cd8bac"
ENV = ROOT / ".env"

lines = ENV.read_text(encoding="utf-8").splitlines()
out = []
seen = False
for ln in lines:
    if ln.startswith("GENLAYER_CONTRACT_ADDRESS"):
        out.append(f"GENLAYER_CONTRACT_ADDRESS={ADDR}")
        seen = True
    else:
        out.append(ln)
if not seen:
    out.append(f"GENLAYER_CONTRACT_ADDRESS={ADDR}")

ENV.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"set GENLAYER_CONTRACT_ADDRESS={ADDR}")
