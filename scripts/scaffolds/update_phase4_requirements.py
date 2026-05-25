"""
Append Phase 4 parsing/fetching deps to backend/requirements.txt.
Idempotent (no duplicate lines).
"""
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
REQ = ROOT / "backend/requirements.txt"

EXTRA = [
    "pypdf==5.1.0",
    "python-docx==1.1.2",
    "beautifulsoup4==4.12.3",
    "lxml==5.3.0",
]

existing = set()
for line in REQ.read_text(encoding="utf-8").splitlines():
    name = line.split("==")[0].strip().lower()
    if name:
        existing.add(name)

with REQ.open("a", encoding="utf-8") as f:
    for spec in EXTRA:
        name = spec.split("==")[0].lower()
        if name in existing:
            print(f"  skip  {spec} (already present)")
            continue
        f.write(spec + "\n")
        print(f"  add   {spec}")

print("done")
