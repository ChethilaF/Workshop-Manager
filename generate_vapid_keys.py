from py_vapid import Vapid

vapid = Vapid()
private_key, public_key = vapid.create_keys()

print("VAPID Public Key:", public_key)
print("VAPID Private Key:", private_key)
