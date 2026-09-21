import getpass
import uuid

import bcrypt

from backend.database import SessionLocal
from backend.models.admin import Admin


def main():
    print("\n=== Create Admin Account ===\n")

    username = input("Admin username: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    if not username or not email or not password:
        print("ERROR: Username, email and password are required.")
        return

    if password != confirm_password:
        print("ERROR: Passwords do not match.")
        return

    if len(password) < 6:
        print("ERROR: Password must contain at least 6 characters.")
        return

    db = SessionLocal()

    try:
        existing_username = (
            db.query(Admin)
            .filter(Admin.username == username)
            .first()
        )

        if existing_username:
            print("ERROR: Username already exists.")
            return

        existing_email = (
            db.query(Admin)
            .filter(Admin.email == email)
            .first()
        )

        if existing_email:
            print("ERROR: Email already exists.")
            return

        admin_id = "ADM-" + uuid.uuid4().hex[:8].upper()

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        admin = Admin(
            admin_id=admin_id,
            username=username,
            email=email,
            password_hash=password_hash,
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("\nAdmin account created successfully.")
        print(f"Admin ID : {admin.admin_id}")
        print(f"Username : {admin.username}")
        print(f"Email    : {admin.email}")
        print(f"Active   : {admin.is_active}")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
