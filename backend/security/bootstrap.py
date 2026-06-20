"""Create the first MedicalOfficer account without putting secrets in files."""

from __future__ import annotations

import argparse
import getpass

from backend.db import crud
from backend.db.models import UserRole
from backend.db.session import SessionLocal, init_db
from backend.security.auth import hash_password


def main() -> int:
	parser = argparse.ArgumentParser(description="Bootstrap a MedicalOfficer account")
	parser.add_argument("--user-id", required=True)
	parser.add_argument("--username", required=True)
	parser.add_argument("--display-name")
	args = parser.parse_args()
	password = getpass.getpass("Password (minimum 12 characters): ")
	confirmation = getpass.getpass("Confirm password: ")
	if password != confirmation:
		raise SystemExit("Passwords do not match")

	init_db()
	with SessionLocal() as db:
		if crud.get_user_account(db, args.user_id) or crud.get_user_by_username(
			db, args.username
		):
			raise SystemExit("User ID or username already exists")
		crud.create_user_account(
			db,
			{
				"id": args.user_id,
				"username": args.username,
				"password_hash": hash_password(password),
				"role": UserRole.MEDICAL_OFFICER,
				"display_name": args.display_name,
				"active": True,
			},
		)
		db.commit()
	print(f"Created MedicalOfficer account {args.username}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
