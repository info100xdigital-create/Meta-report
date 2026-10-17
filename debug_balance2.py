import re
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

ACCESS_TOKEN = "EAAVZASUWKtZAMBRmw8yvZCIZCPYZCpmVKdnuI7CdvraekQPGZBfLGhaMNWMrcfJYNfND83rZBYR6DdIf0B0eYO6nFIFYr7JuEZCnmhvZCVrQ83mRMMfNY0R31hMtQKxXn068kYrjaaPyE2DhQZCAF42mgRCx0sKO5E3EenJzi4lU3lP7bkVbF2mWWvBuimXyxqw9ZCUnHZCYCqZCIZCbV10b3xDSKtoucyQuGpW2yplYZCHXQyIVRsIeVsl4ZBmF1dwMqZAXNofeO2G3qKM3gIjjidZB1ZAKnBDrqos3AZDZD"
APP_ID       = "1505546117756307"
APP_SECRET   = "4098ec0913fb0618b902e29edad3eb8e"

FacebookAdsApi.init(APP_ID, APP_SECRET, ACCESS_TOKEN)

data = AdAccount("act_1039999246750750").api_get(
    fields=['funding_source_details', 'balance']
)

print("=== FULL RAW DATA ===")
print(dict(data))

print("\n=== FSD OBJECT TYPE ===")
fsd = data.get('funding_source_details', {})
print(f"type = {type(fsd)}")
print(f"fsd  = {fsd}")

print("\n=== ACCESSING DISPLAY_STRING ===")
# Try different access methods
print(f"fsd.get('display_string')          = {fsd.get('display_string') if hasattr(fsd,'get') else 'NO GET METHOD'}")
print(f"fsd['display_string'] (if exists)  = ", end="")
try:    print(fsd['display_string'])
except: print("KeyError — not accessible this way")

# Try export_all_data
print(f"\nfsd export_all_data = ", end="")
try:    print(fsd.export_all_data())
except: print("no export_all_data method")

# Try _data
print(f"\nfsd._data = ", end="")
try:    print(fsd._data)
except: print("no _data")

print(f"\nbalance field raw = {data.get('balance')}")
print(f"balance / 100     = {float(data.get('balance', 0)) / 100:.2f}")