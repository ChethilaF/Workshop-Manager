from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64

with open("vapid_private.pem", "rb") as f:
    privkey = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
    raw_bytes = privkey.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    b64url_key = base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")

print("Paste this into .env as VAPID_PRIVATE_KEY:\n")
print(b64url_key)
