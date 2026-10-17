import os
import re
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime, timedelta
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

# =============================================================
#  CONFIGURATION  — FILL IN YOUR NEW CREDENTIALS BELOW
# =============================================================

# ── STEP 1: Facebook App (create new app → see guide below) ──
APP_ID        = "1146995414370649"
APP_SECRET    = "fcd5ebd33ebb105ba2659d160f2ab5a1"
ACCESS_TOKEN  = "EAAQTL647iVkBS0Ayit7SPNeZAEazCp1YsaBIKZB3wmINAEo9G0MicqDeMBahloxyWDVCDehuqMJKebjBeTntMlSYyZAIZC13iuSK9zYaDtGJu8Wxj29W72aG04VZCZCEWXyk8obmeusRQyIYnk1Wb2w5SZCZARdDsjGsrt4mo9VSIvFFPzvsoKajILHsgvUFAoPh7vtx6yLxCroz7eLkw03BSAXYRaxannxxt4imHokBP9JoaV4fLsh8tZBG5h0ZBZBVVC5IKOxp9FxZCSHHbAy7WCtP"

API_URL       = "https://my.askeva.io/v1/message/send-message"
API_TOKEN     = "4833c7160371e93c91ea9845e14308880627ca7eb14c27e6ebe064659049aae69fba15af4c7ecc415c681673c7a6c8eb5f180d937685dfdc5d03c7dcc8fd8d69"

PHONE_NUMBER  = "919360363056"
TEMPLATE_NAME = "scheduled_meta_ads_report"

# =============================================================
#  ALL CLIENT ACCOUNTS
# =============================================================

AD_ACCOUNTS = {
    "AMPPA"           : "act_955527027072311",
    "Golden Gem"      : "act_1290948562690497",
    "Haseena"         : "act_445771558189790",
    "Victory TATA"    : "act_1120899880156032",
    "V-Elite"         : "act_28819135127776119",
    "Tristar"         : "act_XXXXXXXXXX",         # <-- ADD TRISTAR ID
    "Global Dentistry": "act_715916931079198",
    "Barath Avenue"   : "act_1382301152911804",
    "Paacha Chaalo"   : "act_1249719060614173",
}

# =============================================================
#  AWARENESS OBJECTIVES
# =============================================================

AWARENESS_OBJECTIVES = {
    'BRAND_AWARENESS', 'REACH', 'VIDEO_VIEWS',
    'PAGE_LIKES', 'EVENT_RESPONSES',
    'OUTCOME_AWARENESS',
}

AWARENESS_NAME_KEYWORDS = [
    'awareness', 'brand awareness', 'reach campaign'
]

# =============================================================
#  INIT FACEBOOK SDK
# =============================================================

FacebookAdsApi.init(APP_ID, APP_SECRET, ACCESS_TOKEN)
FacebookAdsApi.get_default_api().SDK_VERSION = "v25.0"

# =============================================================
#  DATE LOGIC
#  Monday    → fetch Saturday + Sunday (combined report)
#  Tue–Sat   → fetch yesterday only
#  Sunday    → skip (holiday)
# =============================================================

today   = datetime.now()
weekday = today.weekday()   # 0=Mon … 5=Sat … 6=Sun

if weekday == 6:
    print("\nToday is Sunday — no report sent.")
    exit()
elif weekday == 0:
    date_since   = (today - timedelta(days=2)).strftime('%Y-%m-%d')  # Saturday
    date_until   = (today - timedelta(days=1)).strftime('%Y-%m-%d')  # Sunday
    report_label = f"{date_since} to {date_until} (Sat + Sun)"
else:
    date_since   = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    date_until   = date_since
    report_label = date_since

yesterday = date_since   # kept for display

print(f"\n{'='*55}")
print(f"  META ADS TEXT REPORT  |  Date: {report_label}")
print(f"{'='*55}\n")

# =============================================================
#  META API HELPERS
# =============================================================

def get_leads(actions):
    for priority in [
        'onsite_conversion.lead_grouped',
        'lead',
        'onsite_conversion.messaging_conversation_started_7d',
    ]:
        for a in actions:
            if a.get('action_type') == priority:
                try:    return int(float(a.get('value', 0)))
                except: return 0
    return 0

def get_cpl(cost_actions):
    for priority in [
        'onsite_conversion.lead_grouped',
        'lead',
        'onsite_conversion.messaging_conversation_started_7d',
    ]:
        for a in cost_actions:
            if a.get('action_type') == priority:
                try:    return round(float(a.get('value', 0)), 2)
                except: return 0
    return 0

def get_ctr(item):
    try:    return round(float(item.get("ctr", 0)), 2)
    except: return 0

def get_balance(account_id):
    """
    Parses Available Balance from funding_source_details.display_string.
    SDK object requires bracket access fsd['key'], not fsd.get().
    e.g. "Available balance (Rs.2,922.68 INR)" -> 2922.68
    """
    try:
        data = AdAccount(account_id).api_get(
            fields=['funding_source_details', 'balance']
        )
        fsd = data.get('funding_source_details')

        if fsd is not None:
            try:
                display = fsd['display_string']
                if display:
                    match = re.search(r'[\d,]+\.?\d*', display)
                    if match:
                        val = round(float(match.group().replace(',', '')), 2)
                        print(f"  Balance: Rs. {val:.2f}")
                        return val
            except Exception as e:
                print(f"  Balance display_string error: {e}")

        raw = float(data.get('balance', 0))
        val = round(raw / 100, 2)
        print(f"  Balance fallback: Rs. {val:.2f}")
        return val

    except Exception as e:
        print(f"  Balance Error: {e}")
        return 0.0

def clean(text):
    text = str(text).replace('\n', ' ').replace('\t', ' ')
    while '     ' in text:
        text = text.replace('     ', '    ')
    return text.strip()

# =============================================================
#  BUILD REPORT BODY
#  Lead campaign  : "CampaignName > Results:X | Spent:Rs.X | CPL:Rs.X"
#  Awareness      : "CampaignName > Reach:X | Spent:Rs.X"
#  Balance line   : "Available Balance:Rs.X"
# =============================================================

def build_body(campaigns, total_leads, total_spent, avg_cpl, balance):
    parts = []
    for row in campaigns:
        if row['is_awareness']:
            parts.append(
                f"{row['campaign_name']} > "
                f"Reach:{row['reach']:,} | "
                f"Spent:Rs.{row['spent']:.2f}"
            )
        else:
            parts.append(
                f"{row['campaign_name']} > "
                f"Results:{row['leads']} | "
                f"Spent:Rs.{row['spent']:.2f} | "
                f"CPL:Rs.{row['cpl']:.2f}"
            )
    parts.append(f"Available Balance:Rs.{balance:.2f}")
    return clean("  |  ".join(parts))

# =============================================================
#  SEND WHATSAPP  (token in URL query param — correct method)
# =============================================================

def send_whatsapp_text(date, account, body):
    payload = {
        "to"  : PHONE_NUMBER,
        "type": "template",
        "template": {
            "language"  : {"policy": "deterministic", "code": "en"},
            "name"      : TEMPLATE_NAME,
            "components": [
                {
                    "type"      : "body",
                    "parameters": [
                        {"type": "text", "text": clean(date)},
                        {"type": "text", "text": clean(account)},
                        {"type": "text", "text": body},
                    ]
                }
            ]
        }
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(
        f"{API_URL}?token={API_TOKEN}",   # token in URL, NOT in header
        headers=headers,
        json=payload,
        verify=False    # bypass SSL hostname mismatch on accounts.100xflow.com
    )

    print(f"  WhatsApp status={response.status_code}")
    if response.status_code not in (200, 201):
        print(f"  Response: {response.text}")

    return response.status_code in (200, 201)

# =============================================================
#  MAIN LOOP
# =============================================================

success_count = 0
fail_count    = 0
skip_count    = 0

for account_name, account_id in AD_ACCOUNTS.items():

    print(f"\n  Fetching {account_name}...")

    try:
        insights = AdAccount(account_id).get_insights(
            params={
                'level'      : 'campaign',
                'time_range' : {'since': date_since, 'until': date_until},
                'filtering'  : [{'field': 'spend', 'operator': 'GREATER_THAN', 'value': 0}],
                'limit'      : 500,
            },
            fields=[
                'campaign_name',
                'objective',
                'spend',
                'reach',
                'ctr',
                'actions',
                'cost_per_action_type',
            ]
        )

        insights_data = list(insights)
        print(f"  Campaigns found: {len(insights_data)}")

        if not insights_data:
            print(f"  No spend data on {yesterday} — skipping")
            skip_count += 1
            continue

        campaigns   = []
        total_leads = 0
        total_spent = 0.0

        for item in insights_data:
            spend     = round(float(item.get('spend', 0)), 2)
            objective = item.get('objective', '').upper()
            camp_name = item.get('campaign_name', '').lower()

            is_aware  = (
                objective in AWARENESS_OBJECTIVES or
                any(kw in camp_name for kw in AWARENESS_NAME_KEYWORDS)
            )

            reach  = int(item.get('reach', 0)) if is_aware else 0
            leads  = 0 if is_aware else get_leads(item.get('actions', []))
            cpl    = 0 if is_aware else get_cpl(item.get('cost_per_action_type', []))
            ctr    = get_ctr(item)

            if not is_aware:
                total_leads += leads
            total_spent += spend

            campaigns.append({
                'campaign_name': item.get('campaign_name', 'N/A'),
                'objective'    : objective,
                'is_awareness' : is_aware,
                'leads'        : leads,
                'reach'        : reach,
                'cpl'          : cpl,
                'ctr'          : ctr,
                'spent'        : spend,
            })

        avg_cpl = round(total_spent / total_leads, 2) if total_leads > 0 else 0.0
        balance = get_balance(account_id)

        # Terminal preview
        print(f"\n  --- PREVIEW ---")
        print(f"  Date   : {yesterday}")
        print(f"  Account: {account_name}")
        for row in campaigns:
            if row['is_awareness']:
                print(f"    {row['campaign_name']} > "
                      f"Reach:{row['reach']:,} | "
                      f"Spent:Rs.{row['spent']:.2f}")
            else:
                print(f"    {row['campaign_name']} > "
                      f"Results:{row['leads']} | "
                      f"Spent:Rs.{row['spent']:.2f} | "
                      f"CPL:Rs.{row['cpl']:.2f}")
        print(f"  Available Balance: Rs.{balance:.2f}")
        print(f"  ---------------")

        body = build_body(campaigns, total_leads, total_spent, avg_cpl, balance)
        sent = send_whatsapp_text(yesterday, account_name, body)

        if sent:
            print(f"  SUCCESS: Sent for {account_name}")
            success_count += 1
        else:
            print(f"  FAILED:  Not sent for {account_name}")
            fail_count += 1

    except Exception as e:
        print(f"  ERROR for {account_name}: {e}")
        fail_count += 1

# =============================================================
#  SUMMARY
# =============================================================

print(f"\n{'='*55}")
print(f"  DONE  |  Sent:{success_count}  |  "
      f"Failed:{fail_count}  |  Skipped:{skip_count}")
print(f"{'='*55}\n")
