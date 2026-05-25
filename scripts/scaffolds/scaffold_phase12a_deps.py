"""
Add prometheus-fastapi-instrumentator and prometheus-client to backend reqs.
"""
from pathlib import Path

REQ = Path("/Users/macbook/CVPilot/backend/requirements.txt")
text = REQ.read_text(encoding="utf-8")
additions = []
for spec in ["prometheus-client==0.21.0", "prometheus-fastapi-instrumentator==7.0.0"]:
    name = spec.split("==")[0]
    if name not in text:
        additions.append(spec)

if additions:
    REQ.write_text(text.rstrip() + "\n" + "\n".join(additions) + "\n", encoding="utf-8")
    for spec in additions:
        print(f"  added {spec}")
else:
    print("already present")
