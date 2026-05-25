# Secrets Rotation Runbook

This runbook covers the four secrets CVPilot relies on. Each has a
different blast radius and a different rotation procedure. Read the
relevant section in full before you start.

## Inventory

| Secret               | Env var                       | Rotation cost | Blast radius                  |
|----------------------|-------------------------------|---------------|-------------------------------|
| App secret key       | APP_SECRET_KEY                | Low           | Invalidates JWTs              |
| JWT signing key      | (derived from APP_SECRET_KEY) | Low           | All users signed out          |
| Database password    | DATABASE_URL                  | Medium        | Downtime during cutover       |
| Wallet Fernet key    | (derived from APP_SECRET_KEY) | HIGH          | Orphans every encrypted key   |

The wallet Fernet key is derived from APP_SECRET_KEY via PBKDF2.
Rotating APP_SECRET_KEY therefore rotates the wallet Fernet key too,
which means every encrypted private key in the database becomes
unreadable. See the dedicated section below.

## 1. JWT signing key (cheap, routine)

The JWT signing key is APP_SECRET_KEY. To rotate without affecting
wallet encryption, you would need to split them first (see Appendix A).
Until that split lands, rotating JWT means rotating wallet encryption.

If wallet encryption is split out, the procedure is:

1. Generate a new 64+ char secret: openssl rand -base64 48
2. Update the secret in the orchestrator (Fly.io secrets / Render env).
3. Roll the API service. All active JWTs are invalidated; users sign in
   again.
4. Confirm /readyz returns 200 and cvpilot_evaluations_total is still
   incrementing.

## 2. Database password

1. Create a new role with the same grants, or set a new password on
   the existing role.
2. Update DATABASE_URL in the orchestrator.
3. Roll the API and worker services together (they share the DSN).
4. Drop the old credential once both deployments show database: true
   on /readyz for at least one full Prometheus scrape interval.

## 3. Wallet Fernet key (HIGH RISK)

The wallet Fernet key is derived from APP_SECRET_KEY via PBKDF2 with
a fixed salt. Every user's private key on disk is encrypted under this
key. Rotating APP_SECRET_KEY without re-encrypting first will brick
every user's wallet.

Procedure:

1. Freeze writes. Put the API in read-only mode or take a brief outage
   window. New registrations during rotation would be encrypted under
   the wrong key.
2. Backup. Snapshot the database. This is the single point of
   no return.
3. Run the re-encrypt script (sketch below). For each user, decrypt
   under the old key, then encrypt under the new key, then commit.
4. Atomically swap the secret in the orchestrator and roll the API.
5. Smoke test. Sign in as a known user, hit GET /wallet, confirm the
   address matches and the balance loads.
6. Unfreeze writes.

### Re-encrypt script outline

    # scripts/rotate_wallet_key.py  (not committed; generate per rotation)
    from cryptography.fernet import Fernet
    from backend.app.core.wallet_crypto import derive_fernet_key
    from backend.app.db.session import SessionLocal
    from backend.app.models.user import User
    from sqlalchemy import select

    OLD_SECRET = "..."   # the secret currently live
    NEW_SECRET = "..."   # the secret you are rotating to

    old = Fernet(derive_fernet_key(OLD_SECRET))
    new = Fernet(derive_fernet_key(NEW_SECRET))

    db = SessionLocal()
    for u in db.execute(select(User)).scalars():
        if not u.encrypted_private_key:
            continue
        plaintext = old.decrypt(u.encrypted_private_key.encode())
        u.encrypted_private_key = new.encrypt(plaintext).decode()
    db.commit()

Test this against a database snapshot before running it against
production.

## Appendix A: splitting JWT key from wallet key

Recommended follow-up. Introduce WALLET_FERNET_SECRET as a separate
env var, falling back to APP_SECRET_KEY for backward compatibility.
Once every user record has been re-encrypted under the new variable,
rotating JWT is independent of wallet encryption.
