import gzip
import json
import requests

from .models import Device


EXPO_NOTIFICATION_URL = "https://exp.host/--/api/v2/push/send"


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def broadcast(title: str, body: str):
    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate",
        "content-type": "application/json",
        "content-encoding": "gzip"
    }

    devices = Device.query.all()

    for chunk in chunks(devices, 100):
        # Generate message for each target device
        messages = [{"to": device.expo_push_token,
                     "sound": "default", "title": title, "body": body}
                    for device in chunk]

        # Compress request body to reduce overhead with many registered devices
        body = gzip.compress(json.dumps(messages).encode("utf-8"))

        # Send notification to expo
        requests.post(EXPO_NOTIFICATION_URL, headers=headers, data=body)
