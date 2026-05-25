"""
Scope test_admin_can_list_applications_empty to the test user's applications
only, so it stays correct in environments that already have real (founder)
applications in the DB.
"""
from pathlib import Path

TARGET = Path("/Users/macbook/CVPilot/tests/backend/test_admin.py")
text = TARGET.read_text(encoding="utf-8")

OLD = '''def test_admin_can_list_applications_empty(client) -> None:
    _, token = _register_and_token(client, promote=True)
    r = client.get(
        "/api/v1/admin/applications",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    assert r.json() == []
'''

NEW = '''def test_admin_can_list_applications_for_user(client) -> None:
    """Filter by the freshly-registered test user's id; that user must have
    zero applications even when the global list has rows from real users."""
    _, token = _register_and_token(client, promote=True)
    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    ).json()
    r = client.get(
        f"/api/v1/admin/applications?user_id={me['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    assert r.json() == []
'''

if OLD in text:
    TARGET.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print(f"patched {TARGET.name}: scoped admin list test to the test user's id")
else:
    print("no change needed (test already updated)")
