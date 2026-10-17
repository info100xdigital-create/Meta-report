from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

ACCESS_TOKEN = "EAAVZASUWKtZAMBRmw8yvZCIZCPYZCpmVKdnuI7CdvraekQPGZBfLGhaMNWMrcfJYNfND83rZBYR6DdIf0B0eYO6nFIFYr7JuEZCnmhvZCVrQ83mRMMfNY0R31hMtQKxXn068kYrjaaPyE2DhQZCAF42mgRCx0sKO5E3EenJzi4lU3lP7bkVbF2mWWvBuimXyxqw9ZCUnHZCYCqZCIZCbV10b3xDSKtoucyQuGpW2yplYZCHXQyIVRsIeVsl4ZBmF1dwMqZAXNofeO2G3qKM3gIjjidZB1ZAKnBDrqos3AZDZD"
APP_ID       = "1505546117756307"
APP_SECRET   = "4098ec0913fb0618b902e29edad3eb8e"

FacebookAdsApi.init(APP_ID, APP_SECRET, ACCESS_TOKEN)

account_id = "act_1039999246750750"

data = AdAccount(account_id).api_get(
    fields=[
        'balance',
        'funding_source_details',
        'spend_cap',
        'amount_spent',
        'currency',
    ]
)

print("\n=== RAW API RESPONSE ===")
for key, val in data.items():
    print(f"  {key} = {val}")

print("\n=== BALANCE CALCULATIONS ===")
raw_balance = float(data.get('balance', 0))
print(f"  balance field raw  = {raw_balance}")
print(f"  balance / 100      = {round(raw_balance / 100, 2)}")
print(f"  balance as-is      = {round(raw_balance, 2)}")

fsd = data.get('funding_source_details', {})
print(f"\n  funding_source_details = {fsd}")
if fsd and fsd.get('amount') is not None:
    raw_fsd = float(fsd['amount'])
    print(f"  fsd.amount raw     = {raw_fsd}")
    print(f"  fsd.amount / 100   = {round(raw_fsd / 100, 2)}")
    print(f"  fsd.amount as-is   = {round(raw_fsd, 2)}")

print(f"\n  TARGET = Rs. 3269.51")
print("  Match the TARGET above to find the correct field + calculation")