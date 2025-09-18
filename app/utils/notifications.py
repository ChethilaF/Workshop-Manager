import os  # For accessing environment variables (VAPID keys)
import json  # For converting Python dicts to JSON strings
from pywebpush import webpush, WebPushException
from app import db  # SQLAlchemy database instance for managing subscriptions


def send_push_to_technician(technician_id, title, body, url="/"):
    """
    Sends a push notification to all
    active subscriptions for a given technician.

    Parameters:
    - technician_id (int): ID of the technician to notify
    - title (str): Notification title
    - body (str): Notification message/body
    - url (str): Optional URL to open w`hen the notification is clicked
    """
    # Importing the PushSubscription model locally to avoid circular imports
    from app.models import PushSubscription

    # Query all active push subscriptions for this technician
    subs = PushSubscription.query.filter_by(technician_id=technician_id).all()

    # Loop through each subscription and attempt to send a push
    for sub in subs:
        try:
            # Send the push notification using pywebpush
            webpush(
                subscription_info={
                    # The endpoint URL for the push service
                    "endpoint": sub.endpoint,
                    # Encryption keys
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
                },
                # Notification payload
                data=json.dumps({"title": title, "body": body, "url": url}),
                # Private key from environment
                vapid_private_key=os.getenv("VAPID_PRIVATE_KEY"),
                # Contact email
                vapid_claims={"sub": "mailto:chethilafernando77@gmail.com"}
            )
        except WebPushException as ex:
            # Print any push errors for debugging
            print("Push failed:", repr(ex))

            # If subscription is no longer valid, remove it from DB
            if "410" in str(ex) or "404" in str(ex):
                db.session.delete(sub)
                db.session.commit()
