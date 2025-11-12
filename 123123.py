import json
import hmac
import hashlib

body = {
    "hwid": "2CEF0FA4-A1803C78-8FADD7D0-2DD6147A",
    "timestamp": 1762617758,
    "nonce": "uNiquE11"
}
key = b'5f4a39089a01bebf59d525351fd8d88802'
msg = json.dumps(body, sort_keys=True)

signature = hmac.new(
    key,
    msg.encode("utf-8"),
    hashlib.sha256
).hexdigest()

print("JSON для тела:", msg)
print("Подпись:", signature)
