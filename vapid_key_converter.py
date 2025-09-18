import os
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv

load_dotenv()

public_key_pem = os.getenv("VAPID_PUBLIC_KEY")

public_key_pem_clean = public_key_pem.replace("\\n", "\n").encode()

public_key = serialization.load_pem_public_key(public_key_pem_clean, backend=default_backend())

raw_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)

print("Base64 Public Key (use this in browser):")
print(base64.urlsafe_b64encode(raw_bytes).decode("utf-8"))
