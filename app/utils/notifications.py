import os
import json
from pywebpush import webpush, WebPushException
from app.models import PushSubscription

def send_push_to_technician(technician_id, title, body, url="/"):
    subs = PushSubscription.query.filter_by(technician_id=technician_id).all()
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
                },
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=os.getenv("VAPID_PRIVATE_KEY"),
                vapid_claims={"sub": "mailto:chethilafernando77@gmail.com"}
            )
        except WebPushException as ex:
            print("Push failed:", repr(ex))
