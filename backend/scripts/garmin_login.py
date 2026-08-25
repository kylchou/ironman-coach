"""One-time interactive Garmin login.

Run this yourself, from backend/, with the venv active:

    .venv\\Scripts\\activate
    python scripts/garmin_login.py

It asks for your Garmin email and password (and an MFA code, if Garmin asks
for one) directly at the terminal -- nothing is sent anywhere except to
Garmin's own login endpoint, and the password is never written to disk.
On success it caches a session token to backend/.garmin_tokens/ (gitignored)
so the API server can make requests without ever touching your password
again. Re-run this any time that cached session expires or gets revoked.
"""

import getpass
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from garminconnect import Garmin  # noqa: E402

from app.config import settings  # noqa: E402

TOKEN_DIR = Path(__file__).resolve().parents[1] / ".garmin_tokens"


def main() -> None:
    default_email = settings.garmin_email
    prompt = f"Garmin email [{default_email}]: " if default_email else "Garmin email: "
    email = input(prompt).strip() or default_email
    if not email:
        print("Email is required.")
        raise SystemExit(1)

    password = getpass.getpass("Garmin password (not stored, not echoed): ")

    client = Garmin(email, password, prompt_mfa=lambda: input("Enter the MFA code Garmin sent you: ").strip())

    TOKEN_DIR.mkdir(exist_ok=True)
    client.login(tokenstore=str(TOKEN_DIR))

    print(f"Logged in as {client.get_full_name()}.")
    print(f"Session cached at {TOKEN_DIR} -- the API server can now fetch activities without your password.")


if __name__ == "__main__":
    main()
