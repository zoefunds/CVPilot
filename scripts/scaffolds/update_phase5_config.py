"""
Add llm_backend field to backend/app/core/config.py if missing.
"""
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
TARGET = ROOT / "backend/app/core/config.py"

text = TARGET.read_text(encoding="utf-8")

if "llm_backend" in text:
    print("llm_backend already present, no-op")
    raise SystemExit(0)

NEEDLE = '    genlayer_llm_model: str = Field(default="default", alias="GENLAYER_LLM_MODEL")\n'
INSERT = (
    NEEDLE
    + '    llm_backend: Literal["stub", "genlayer"] = Field(default="stub", alias="LLM_BACKEND")\n'
)

if NEEDLE not in text:
    raise SystemExit("anchor line not found in config.py - aborting")

TARGET.write_text(text.replace(NEEDLE, INSERT), encoding="utf-8")
print("patched backend/app/core/config.py")
