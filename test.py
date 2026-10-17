import requests

API_URL = "https://accounts.100xflow.com/v1/message/send-message"

API_KEY = "4833c7160371e93c91ea9845e14308887ab62a57441e079d51fa799f8985f2679e8839394b655bbaf49eaba0d4d2d877d6885cfa6d3966b4dd4921300de9434d"

payload = {
    "token": API_KEY,
    "to": "917092771404",
    "body": "✅ WhatsApp API Test Successful"
}

response = requests.post(API_URL, json=payload)

print("STATUS:", response.status_code)
print("RESPONSE:", response.text)