"""
Replace `.test` TLD with `.dev` in test fixtures so email-validator accepts them.
"""

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")

PATCHES = {
    "tests/backend/test_auth.py": (
        '@cvpilot.test',
        '@cvpilot.dev',
    ),
    "tests/backend/conftest.py": (
        "pytest+%@cvpilot.test",
        "pytest+%@cvpilot.dev",
    ),
}


def main() -> None:
    for rel, (old, new) in PATCHES.items():
        p = ROOT / rel
        text = p.read_text(encoding="utf-8")
        if old not in text:
            print(f"  skip  {rel} (token not found)")
            continue
        p.write_text(text.replace(old, new), encoding="utf-8")
        print(f"  patched {rel}")


if __name__ == "__main__":
    main()
