"""
diagnose_token.py
==================
Run this on your machine to find out EXACTLY why appsecret_proof
fails. This calls Meta's own debug_token endpoint, which tells us
which app a token actually belongs to — the #1 cause of
"Invalid appsecret_proof" errors.

Usage:
    python diagnose_token.py
"""

import hashlib
import hmac
import requests

# =============================================================
#  PASTE YOUR CURRENT VALUES HERE
# =============================================================
APP_ID       = "1668949257788940"      # Reporting Automation app ID
APP_SECRET   = "a08dd86d56c0f3ce2fa3b5fe9c36c905"
ACCESS_TOKEN = "EAAXt5oeongwBRs0Sk8YzJUZAvQZCJyCOyhI2AUVPhhKZBJvS4LnOixZC0UlJsQZCJJN9w9q1Uh2CwDB42Gp79wwXeVaG6hkgJfsGlnXbHIZCzfdFYtXu73QZAhq1pVHwHxrJtFwvjZCTl3etHjbZBsnRpUKZC1vMG92wxTYfA0Q5nYs5uUBYjXhFVrFdFtbH4bbOOr"

# =============================================================
#  TEST 1 — Compute appsecret_proof locally
# =============================================================
proof = hmac.new(
    APP_SECRET.encode('utf-8'),
    msg=ACCESS_TOKEN.encode('utf-8'),
    digestmod=hashlib.sha256
).hexdigest()

print("\n" + "="*60)
print("  TEST 1: Locally computed appsecret_proof")
print("="*60)
print(f"  {proof}")

# =============================================================
#  TEST 2 — Ask Meta which app this token ACTUALLY belongs to
#  This is the critical test. If app_id below does not match
#  APP_ID above, that is the entire bug.
# =============================================================
print("\n" + "="*60)
print("  TEST 2: Asking Meta which app owns this token")
print("="*60)

app_access_token = f"{APP_ID}|{APP_SECRET}"

try:
    r = requests.get(
        "https://graph.facebook.com/v21.0/debug_token",
        params={
            "input_token": ACCESS_TOKEN,
            "access_token": app_access_token,
        },
        timeout=15,
    )
    data = r.json()
    print(f"  HTTP Status: {r.status_code}")

    if "data" in data:
        token_app_id = data["data"].get("app_id")
        token_type   = data["data"].get("type")
        is_valid     = data["data"].get("is_valid")
        scopes       = data["data"].get("scopes", [])
        expires_at   = data["data"].get("expires_at", 0)
        granular     = data["data"].get("granular_scopes", [])

        print(f"\n  Token belongs to app_id : {token_app_id}")
        print(f"  Your APP_ID in script   : {APP_ID}")
        print(f"  MATCH                   : {'YES — correct!' if str(token_app_id) == str(APP_ID) else 'NO — THIS IS THE BUG!'}")
        print(f"\n  Token type              : {token_type}")
        print(f"  Token is_valid          : {is_valid}")
        print(f"  Expires at (0=never)    : {expires_at}")
        print(f"  Scopes                  : {scopes}")

        if granular:
            print(f"\n  Granular ad account access:")
            for g in granular:
                if g.get("scope") == "ads_read" or g.get("scope") == "ads_management":
                    print(f"    {g.get('scope')}: {g.get('target_ids', 'ALL')}")
    else:
        print(f"\n  ERROR RESPONSE:")
        print(f"  {data}")

except Exception as e:
    print(f"  Request failed: {e}")

# =============================================================
#  TEST 3 — Actually call the Ads API with the proof, raw requests
#  (bypasses the SDK entirely so we see the REAL error)
# =============================================================
print("\n" + "="*60)
print("  TEST 3: Direct API call bypassing the SDK")
print("="*60)

try:
    r2 = requests.get(
        "https://graph.facebook.com/v21.0/me",
        params={
            "access_token": ACCESS_TOKEN,
            "appsecret_proof": proof,
        },
        timeout=15,
    )
    print(f"  HTTP Status: {r2.status_code}")
    print(f"  Response: {r2.json()}")
except Exception as e:
    print(f"  Request failed: {e}")

# =============================================================
#  TEST 4 — Try WITHOUT appsecret_proof at all
#  (works only if "Require App Secret" is OFF in app settings)
# =============================================================
print("\n" + "="*60)
print("  TEST 4: Call WITHOUT appsecret_proof")
print("="*60)

try:
    r3 = requests.get(
        "https://graph.facebook.com/v21.0/me",
        params={"access_token": ACCESS_TOKEN},
        timeout=15,
    )
    print(f"  HTTP Status: {r3.status_code}")
    print(f"  Response: {r3.json()}")
except Exception as e:
    print(f"  Request failed: {e}")

print("\n" + "="*60)
print("  DIAGNOSIS SUMMARY")
print("="*60)
print("""
  If TEST 2 shows app_id MISMATCH:
      -> You generated the System User token while a DIFFERENT
         app was selected in the dropdown. Regenerate the token
         and make sure "Reporting Automation" (1505546117756307)
         is selected before clicking Generate Token.

  If TEST 2 app_id MATCHES but TEST 3 still fails:
      -> The System User does not have the ad accounts assigned
         to it. Go to Business Settings -> System Users ->
         click the system user -> Assigned Assets -> Ad Accounts
         -> Add all 12 client accounts with Full Control.

  If TEST 3 fails but TEST 4 succeeds:
      -> "Require App Secret" is actually OFF correctly, and you
         should simply remove APP_SECRET from FacebookAdsApi.init()
         calls, OR pass appsecret_proof=False to bypass it via the
         SDK's debug parameter.

  If ALL tests fail with the SAME error:
      -> The token itself is invalid/expired. Generate a fresh one.
""")

# =============================================================
#  PLAIN-LANGUAGE ONE-LINE VERDICT
# =============================================================
print("="*60)
print("  FINAL VERDICT")
print("="*60)

try:
    app_match = "data" in data and str(data["data"].get("app_id")) == str(APP_ID)
except Exception:
    app_match = False

try:
    test3_ok = r2.status_code == 200
except Exception:
    test3_ok = False

try:
    test4_ok = r3.status_code == 200
except Exception:
    test4_ok = False

if not app_match:
    print("  >>> ACTION NEEDED: Regenerate the token. When the app")
    print("      selection dialog appears, you must pick")
    print("      'Reporting Automation' — not any other app name.")
elif app_match and not test3_ok and test4_ok:
    print("  >>> ACTION NEEDED: Remove APP_SECRET from")
    print("      FacebookAdsApi.init() in both main.py and")
    print("      image_report.py. Use only:")
    print("      FacebookAdsApi.init(APP_ID, access_token=ACCESS_TOKEN)")
elif app_match and not test3_ok and not test4_ok:
    print("  >>> ACTION NEEDED: The System User does not have the")
    print("      12 ad accounts assigned. Go back to System Users ->")
    print("      this system user -> Add Assets -> Ad Accounts ->")
    print("      add all 12 client accounts with Full Control,")
    print("      THEN regenerate the token again.")
elif app_match and test3_ok:
    print("  >>> Token works correctly outside the SDK!")
    print("      The bug is purely in how the SDK is initialized.")
    print("      Fix: pass app_secret=None and instead set the")
    print("      proof manually via requests.Session, OR remove")
    print("      APP_SECRET entirely from FacebookAdsApi.init().")
else:
    print("  >>> Inconclusive — paste the full output back to Claude.")