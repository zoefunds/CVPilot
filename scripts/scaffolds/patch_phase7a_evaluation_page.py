"""
Insert <RewritePanel /> into the existing evaluation detail page,
right above the closing of the EvaluationView's main returned tree.
"""

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
TARGET = ROOT / "frontend/src/app/dashboard/applications/[id]/page.tsx"

text = TARGET.read_text(encoding="utf-8")

# 1) Add the import if not present.
if "RewritePanel" not in text:
    anchor = "from '@/components/dashboard/StatusBadge';"
    text = text.replace(
        anchor,
        anchor + "\nimport { RewritePanel } from '@/components/dashboard/RewritePanel';",
        1,
    )

# 2) Insert the panel right before the Files section in EvaluationView.
needle = "      {(cv || cl) && ("
if "<RewritePanel" not in text and needle in text:
    insertion = (
        "      <RewritePanel application={app} />\n\n"
        + needle
    )
    text = text.replace(needle, insertion, 1)

TARGET.write_text(text, encoding="utf-8")
print("patched evaluation detail page with RewritePanel")
