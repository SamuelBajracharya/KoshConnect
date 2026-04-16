from sqlalchemy.orm import Session

import models
from database import SessionLocal, run_bootstrap_migrations
from encryption_service import (
    encrypt,
    stable_hash,
    looks_encrypted,
    mask_account_number,
)


def migrate_users(db: Session) -> int:
    updated = 0
    users = db.query(models.User).all()
    for user in users:
        changed = False

        if user.phonenumber and not user.phonenumber_encrypted:
            user.phonenumber_encrypted = encrypt(
                user.phonenumber, aad=f"user_phone:{user.user_id}"
            )
            user.phonenumber_hash = stable_hash(user.phonenumber)
            # Keep plaintext temporarily for compatibility with legacy schemas.
            # You can null this field in a later cleanup after verifying constraints.
            changed = True

        if changed:
            updated += 1

    return updated


def migrate_accounts(db: Session) -> int:
    updated = 0
    accounts = db.query(models.Account).all()
    for account in accounts:
        changed = False

        # Legacy rows may only have masked values. We avoid attempting to reconstruct
        # real account numbers; we simply encrypt what is available.
        if not account.account_number_encrypted and account.account_number_masked:
            # Legacy imports often contain only masked numbers like '**' or '****'.
            # Use a per-account deterministic hash to avoid collisions on unique index.
            legacy_hash_input = f"{account.account_id}:{account.account_number_masked}"
            account.account_number_encrypted = encrypt(
                account.account_number_masked,
                aad=f"account_number:{account.account_id}",
            )
            account.account_number_hash = stable_hash(legacy_hash_input)
            account.account_number_masked = mask_account_number(
                account.account_number_masked
            )
            changed = True

        if account.account_number_encrypted and not looks_encrypted(
            account.account_number_encrypted
        ):
            account.account_number_encrypted = encrypt(
                account.account_number_encrypted,
                aad=f"account_number:{account.account_id}",
            )
            changed = True

        if changed:
            updated += 1

    return updated


def run_migration():
    # Ensure legacy databases get required columns before ORM loads mapped fields.
    run_bootstrap_migrations()

    db = SessionLocal()
    try:
        user_count = migrate_users(db)
        account_count = migrate_accounts(db)
        db.commit()
        print(
            f"Migration completed. Users updated: {user_count}, Accounts updated: {account_count}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
