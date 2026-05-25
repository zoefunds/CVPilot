"""
Remove paid/upgrade/free tier language. CVPilot is fully free.
Also sweep for any stray dashes introduced.
"""

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")

# ---------------- Hero.tsx ----------------
HERO_PATH = ROOT / "frontend/src/components/marketing/Hero.tsx"
hero = HERO_PATH.read_text(encoding="utf-8")

OLD_HERO_LINE = (
    '            <p className="mt-5 text-xs text-[#3a342c]/70">\n'
    '              No credit card. Free tier covers your first 3 evaluations.\n'
    '            </p>\n'
)
NEW_HERO_LINE = (
    '            <p className="mt-5 text-xs text-[#3a342c]/70">\n'
    '              Free to use. No sign up wall on the first evaluation.\n'
    '            </p>\n'
)
assert OLD_HERO_LINE in hero, "Hero anchor not found"
hero = hero.replace(OLD_HERO_LINE, NEW_HERO_LINE)
HERO_PATH.write_text(hero, encoding="utf-8")
print("patched Hero.tsx")


# ---------------- page.tsx (ClosingCTA) ----------------
PAGE_PATH = ROOT / "frontend/src/app/page.tsx"
page = PAGE_PATH.read_text(encoding="utf-8")

OLD_CTA = (
    "            Upload your CV, drop in the job URL, and we deliver a consensus\n"
    "            scored breakdown in under a minute. Free for your first three\n"
    "            evaluations.\n"
)
NEW_CTA = (
    "            Upload your CV, drop in the job URL, and we deliver a consensus\n"
    "            scored breakdown in under a minute. Always free.\n"
)
assert OLD_CTA in page, "ClosingCTA anchor not found"
page = page.replace(OLD_CTA, NEW_CTA)
PAGE_PATH.write_text(page, encoding="utf-8")
print("patched page.tsx (ClosingCTA)")


# ---------------- Features.tsx (Premium card -> AI rewriting) ----------------
FEAT_PATH = ROOT / "frontend/src/components/marketing/Features.tsx"
feat = FEAT_PATH.read_text(encoding="utf-8")

OLD_FEAT = (
    "  {\n"
    "    title: 'Premium AI rewriting',\n"
    "    body: 'When you upgrade, the same engine that scored you rewrites your CV and drafts an interview grade cover letter, tuned to the posting.',\n"
    "  },\n"
)
NEW_FEAT = (
    "  {\n"
    "    title: 'AI rewriting on demand',\n"
    "    body: 'The same engine that scored you rewrites your CV and drafts an interview ready cover letter, tuned to the posting. Free, just like the rest.',\n"
    "  },\n"
)
assert OLD_FEAT in feat, "Premium feature anchor not found"
feat = feat.replace(OLD_FEAT, NEW_FEAT)
FEAT_PATH.write_text(feat, encoding="utf-8")
print("patched Features.tsx")


print("\nDone. Free-tier and premium language removed.")
