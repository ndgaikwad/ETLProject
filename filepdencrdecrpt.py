import sys
import os
import base64
import getpass

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

SALT_SIZE = 16
ITERATIONS = 100_000


def generate_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS
    )

    return base64.urlsafe_b64encode(
        kdf.derive(password.encode("utf-8"))
    )


def check_output_file(output_file, force=False):
    if os.path.exists(output_file) and not force:
        print(f"ERROR: Output file already exists: {output_file}")
        print("Use --force to overwrite.")
        sys.exit(1)


def encrypt_file(file_path, password, force=False):

    if not os.path.isfile(file_path):
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    output_file = file_path + ".enc"

    check_output_file(output_file, force)

    salt = os.urandom(SALT_SIZE)

    key = generate_key(password, salt)

    cipher = Fernet(key)

    with open(file_path, "rb") as f:
        file_data = f.read()

    encrypted_data = cipher.encrypt(file_data)

    with open(output_file, "wb") as f:
        f.write(salt + encrypted_data)

    print("Encryption successful")
    print(f"Input : {file_path}")
    print(f"Output: {output_file}")


def decrypt_file(file_path, password, force=False):

    if not os.path.isfile(file_path):
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    with open(file_path, "rb") as f:
        encrypted_file = f.read()

    salt = encrypted_file[:SALT_SIZE]
    encrypted_data = encrypted_file[SALT_SIZE:]

    key = generate_key(password, salt)

    cipher = Fernet(key)

    output_file = (
        file_path[:-4]
        if file_path.endswith(".enc")
        else file_path + ".dec"
    )

    check_output_file(output_file, force)

    try:
        decrypted_data = cipher.decrypt(encrypted_data)

        with open(output_file, "wb") as f:
            f.write(decrypted_data)

        print("Decryption successful")
        print(f"Input : {file_path}")
        print(f"Output: {output_file}")

    except Exception:
        print("ERROR: Invalid password or corrupted file")
        sys.exit(1)


def usage():
    print("""
Usage:

Encrypt:
    python filepdencrdecrpt.py encrypt "C:\\Temp\\sample.txt"

Decrypt:
    python filepdencrdecrpt.py decrypt "C:\\Temp\\sample.txt.enc"

Overwrite existing output:
    python filepdencrdecrpt.py encrypt "C:\\Temp\\sample.txt" --force

    python filepdencrdecrpt.py decrypt "C:\\Temp\\sample.txt.enc" --force
""")
    sys.exit(1)


def main():

    force = "--force" in sys.argv

    args = [arg for arg in sys.argv[1:] if arg != "--force"]

    if len(args) != 2:
        usage()

    action = args[0].lower()
    file_path = args[1]

    password = getpass.getpass("Enter password: ")

    if not password:
        print("ERROR: Password cannot be empty")
        sys.exit(1)

    if action == "encrypt":
        encrypt_file(file_path, password, force)

    elif action == "decrypt":
        decrypt_file(file_path, password, force)

    else:
        usage()


if __name__ == "__main__":
    main()