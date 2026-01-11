import json
import hashlib


def digest(fingerprint):
    return hashlib.sha384(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()
