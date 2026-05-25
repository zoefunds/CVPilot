"""
Restore premium AI rewriting feature card. CVPilot is free to use,
but the positioning is premium.
"""

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FEAT_PATH = ROOT / "frontend/src/components/marketing/Features.tsx"
feat = FEAT_PATH.read_text(encoding="utf-8")

OLD = (
    "  {\n"
    "    title: 'AI rewriting on demand',\n"
    "    body: 'The same engine that scored you rewrites your CV and drafts an interview ready cover letter, tuned to the posting. Free, just like the rest.',\n"
    "  },\n"
)
NEW = (
    "  {\n"
    "    title: 'Premium AI rewriting',\n"
    "    body: 'The same engine that scored you rewrites your CV and drafts an interview ready cover letter, tuned precisely to the posting. Premium quality output, free for every user.',\n"
    "  },\n"
)

assert OLD in feat, "Anchor not found"
FEAT_PATH.write_text(feat.replace(OLD, NEW), encoding="utf-8")
print("restored Premium AI rewriting card with free positioning")
