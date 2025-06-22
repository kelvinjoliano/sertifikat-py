import base64

with open("service_account_credentials.json", "r") as f:
    data = f.read()

encoded = base64.b64encode(data.encode()).decode()
print(encoded)