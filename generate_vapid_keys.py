from py_vapid import Vapid01
import base64
from cryptography.hazmat.primitives import serialization


def generate_keys():
    vapid = Vapid01()
    vapid.generate_keys()

    private_pem = vapid.private_pem()
    public_pem = vapid.public_pem()

    with open("vapid_private.pem", "wb") as f:
        f.write(private_pem)
    with open("vapid_public.pem", "wb") as f:
        f.write(public_pem)

    public_key = vapid.public_key
    raw_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    base64_public = base64.urlsafe_b64encode(raw_bytes).decode("utf-8")

    print("Keys generated")
    print("VAPID_PRIVATE_KEY (PEM saved to vapid_private.pem)")
    print(private_pem.decode())
    print("VAPID_PUBLIC_KEY (PEM saved to vapid_public.pem)")
    print(public_pem.decode())
    print("Base64 Public Key (use in browser, save in .env):")
    print(base64_public)


if __name__ == "__main__":
    generate_keys()
