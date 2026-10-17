import os
import re
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

# =============================================================
#  CONFIGURATION
# =============================================================

APP_ID        = "1146995414370649"
APP_SECRET    = "fcd5ebd33ebb105ba2659d160f2ab5a1"
ACCESS_TOKEN  = "EAAQTL647iVkBSyK2L8B9uBmBD3K9uiPTMT1iKUxDC95W2KZBqFynNbsdD072aJtgraipMKwfc1s7b7XrJOJcrwf953ZCZC7LhWREKGFpZBHrjeIYOmKyOAagi3CwFAiAtBQlpZAmDO2pBI7aL83HeGRfn3muo0wEEG6HzGmCN0gBla7BEI0fxKpO4O33rAkcZB5sR9JNI9wWACUqBzmZC1IqrKfZCZC9CutKgkAycAFsZAu8sgdvIchS7pwtYEGTSuZAbRIjtPt8lyzBM7fKdEVrvd7GwZDZD"

API_URL       = "https://backend.askeva.io/v1/message/send-message"
API_TOKEN     = "4833c7160371e93c91ea9845e14308880627ca7eb14c27e6ebe064659049aae69fba15af4c7ecc415c681673c7a6c8eb5f180d937685dfdc5d03c7dcc8fd8d69"

PHONE_NUMBER  = "919360363056"
TEMPLATE_NAME = "scheduled_meta_ads_report_image"

CLOUD_NAME    = "dfcmienp8"
UPLOAD_PRESET = "ml_default"

LOGO_CANDIDATES = ["Logo.png", "logo.png", "logo.PNG", "logo.jpg", "logo.jpeg", "LOGO.PNG"]

# =============================================================
#  CLIENT AD ACCOUNTS
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
#  Monday  → Sat + Sun combined
#  Tue–Sat → yesterday only
#  Sunday  → skip
# =============================================================

today   = datetime.now()
weekday = today.weekday()   # 0=Mon … 6=Sun

if weekday == 6:
    print("\nToday is Sunday — no report sent.")
    exit()
elif weekday == 0:
    date_since   = (today - timedelta(days=2)).strftime('%Y-%m-%d')
    date_until   = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    report_label = f"{date_since} to {date_until} (Sat + Sun)"
else:
    date_since   = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    date_until   = date_since
    report_label = date_since

yesterday = date_since

print(f"\n{'='*55}")
print(f"  META ADS IMAGE REPORT  |  Date: {report_label}")
print(f"{'='*55}\n")

os.makedirs("reports", exist_ok=True)

# =============================================================
#  FONTS
# =============================================================

def load_font(bold=False, size=20):
    bold_paths = [
        "arialbd.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "DejaVuSans-Bold.ttf",
    ]
    normal_paths = [
        "arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans.ttf",
    ]
    for p in (bold_paths if bold else normal_paths):
        try:
            return ImageFont.truetype(p, size)
        except:
            pass
    return ImageFont.load_default()

F_TITLE  = load_font(bold=True,  size=38)
F_HEADER = load_font(bold=True,  size=22)
F_NORMAL = load_font(bold=False, size=20)
F_VALUE  = load_font(bold=True,  size=34)
F_SMALL  = load_font(bold=False, size=16)
F_BRAND  = load_font(bold=True,  size=18)
F_LOGO_B = load_font(bold=True,  size=30)
F_LOGO_S = load_font(bold=False, size=14)

# =============================================================
#  COLORS
# =============================================================

NAVY     = (16,  28, 100)
ORANGE   = (255, 107,   0)
GREEN    = ( 10, 155,  74)
WHITE    = (255, 255, 255)
LIGHT_BG = (245, 246, 250)
BORDER   = (220, 222, 235)
TEXT_MID = ( 90,  95, 120)
ROW_ALT  = (240, 242, 248)
SHADOW   = (205, 208, 225)

# =============================================================
#  DRAW HELPERS
# =============================================================

def tw(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]

def center_text(draw, text, cx, y, font, fill):
    draw.text((cx - tw(draw, text, font) // 2, y), text, font=font, fill=fill)

def wrap_px(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        test = (cur + " " + word).strip()
        if tw(draw, test, font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines

# =============================================================
#  LOGO
# =============================================================

def draw_logo(img, draw, x, y, LW=195, LH=74):
    draw.rounded_rectangle([x, y, x + LW, y + LH], radius=10, fill=WHITE)
    for path in LOGO_CANDIDATES:
        if os.path.exists(path):
            try:
                logo = Image.open(path).convert("RGBA")
                logo.thumbnail((LW - 16, LH - 12), Image.LANCZOS)
                base = Image.new("RGBA", (LW, LH), (255, 255, 255, 255))
                paste_x = (LW - logo.width)  // 2
                paste_y = (LH - logo.height) // 2
                base.paste(logo, (paste_x, paste_y), logo)
                img.paste(base.convert("RGB"), (x, y))
                print(f"  Logo loaded: {path}")
                return
            except Exception as e:
                print(f"  Logo load error ({path}): {e}")
    # Text fallback
    draw.text((x + 12, y + 6),       "The",      font=F_LOGO_S, fill=TEXT_MID)
    draw.text((x + 12, y + 22),      "100",      font=F_LOGO_B, fill=NAVY)
    x2 = x + 12 + tw(draw, "100", F_LOGO_B)
    draw.text((x2,     y + 22),      "X",        font=F_LOGO_B, fill=ORANGE)
    draw.text((x + 12, y + LH - 20), ".Digital", font=F_LOGO_S, fill=TEXT_MID)
    print("  Logo: text fallback")

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

# =============================================================
#  CREATE REPORT IMAGE
# =============================================================

def create_report_image(account_name, report_date, campaigns,
                        total_leads, total_spent, avg_cpl, balance, total_reach=0):
    W          = 1200
    PAD        = 44
    HEADER_H   = 112
    META_H     = 86
    STATS_H    = 150
    TABLE_ROW  = 66
    TABLE_HEAD = 56
    FOOTER_H   = 82
    GAP        = 22
    LABEL_H    = 46

    n_rows  = max(len(campaigns), 1)
    TABLE_H = TABLE_HEAD + n_rows * TABLE_ROW + 14

    H = (HEADER_H + META_H + GAP
         + STATS_H + GAP
         + LABEL_H + GAP // 2
         + TABLE_H + GAP
         + FOOTER_H + 10)

    img  = Image.new("RGB", (W, H), LIGHT_BG)
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, W, HEADER_H], fill=NAVY)
    draw.text((PAD, 26), "THE 100X.DIGITAL", font=F_TITLE, fill=WHITE)
    dx = PAD + tw(draw, "THE 100X.DIGITAL", F_TITLE) + 16
    draw.text((dx, 26), "-  META ADS REPORT", font=F_TITLE, fill=ORANGE)
    LW, LH = 195, 74
    lx = W - PAD - LW
    ly = (HEADER_H - LH) // 2
    draw_logo(img, draw, lx, ly, LW, LH)
    draw.rectangle([0, HEADER_H - 5, W, HEADER_H], fill=ORANGE)

    # Meta strip
    my = HEADER_H
    draw.rectangle([0, my, W, my + META_H], fill=WHITE)
    draw.line([0, my + META_H - 1, W, my + META_H - 1], fill=BORDER, width=1)
    py = my + 17

    def pill(x, w, label, value, bg, lc, vc, bc=BORDER):
        draw.rounded_rectangle([x, py, x + w, py + 54], radius=8, fill=bg, outline=bc, width=1)
        draw.text((x + 14, py + 9),  label, font=F_SMALL, fill=lc)
        draw.text((x + 14, py + 30), value, font=F_BRAND, fill=vc)

    pill(PAD,       216, "Date",    report_date,   LIGHT_BG, TEXT_MID, NAVY)
    pill(PAD + 232, 290, "Account", account_name,  LIGHT_BG, TEXT_MID, NAVY)

    bal_text  = f"Rs. {balance:.2f}"
    bal_label = "Available Balance"
    bal_tw    = tw(draw, bal_text,  F_HEADER)
    lbl_tw    = tw(draw, bal_label, F_SMALL)
    bpw       = max(bal_tw, lbl_tw) + 36
    bpx       = W - PAD - bpw
    draw.rounded_rectangle([bpx - 3, py - 3, bpx + bpw + 3, py + 57], radius=10, fill=ORANGE)
    draw.rounded_rectangle([bpx,     py,     bpx + bpw,     py + 54], radius=8,  fill=NAVY)
    lbl_x = bpx + (bpw - lbl_tw) // 2
    draw.text((lbl_x, py + 7),  bal_label, font=F_SMALL,  fill=(200, 210, 255))
    val_x = bpx + (bpw - bal_tw) // 2
    draw.text((val_x, py + 27), bal_text,  font=F_HEADER, fill=ORANGE)

    # Summary cards
    sy = my + META_H + GAP
    cw = (W - 2 * PAD - 2 * GAP) // 3

    if total_leads > 0:
        first_card = ("Total Leads", str(total_leads), GREEN)
    elif total_reach > 0:
        first_card = ("Total Reach", f"{total_reach:,}", GREEN)
    else:
        first_card = ("Total Leads", str(total_leads), GREEN)

    cards = [
        first_card,
        ("Amount Spent",     f"Rs. {total_spent:.2f}", ORANGE),
        ("Avg. Cost / Lead", f"Rs. {avg_cpl:.2f}",     NAVY),
    ]

    for i, (label, value, accent) in enumerate(cards):
        cx = PAD + i * (cw + GAP)
        draw.rounded_rectangle([cx + 3, sy + 3, cx + cw + 3, sy + STATS_H + 3], radius=14, fill=SHADOW)
        draw.rounded_rectangle([cx,     sy,     cx + cw,     sy + STATS_H],     radius=14, fill=WHITE)
        draw.rounded_rectangle([cx, sy, cx + cw, sy + 8], radius=0, fill=accent)
        draw.text((cx + 20, sy + 22), label, font=F_SMALL, fill=TEXT_MID)
        draw.text((cx + 20, sy + 60), value, font=F_VALUE, fill=accent)

    # Campaign table
    ty = sy + STATS_H + GAP
    draw.text((PAD, ty + 6), "Campaign Performance", font=F_HEADER, fill=NAVY)
    uw = tw(draw, "Campaign Performance", F_HEADER)
    draw.line([PAD, ty + LABEL_H - 4, PAD + uw, ty + LABEL_H - 4], fill=ORANGE, width=3)
    ty += LABEL_H + GAP // 2

    draw.rounded_rectangle([PAD - 2, ty - 2, W - PAD + 2, ty + TABLE_H + 2], radius=10, fill=SHADOW)
    draw.rounded_rectangle([PAD,     ty,     W - PAD,     ty + TABLE_H],     radius=10, fill=WHITE)

    cols = [
        ("#",           PAD + 10,  34,  "c"),
        ("Campaign",    PAD + 56,  448, "l"),
        ("Results",     624,        90, "c"),
        ("CPL (Rs.)",   730,       142, "c"),
        ("CTR %",       888,        90, "c"),
        ("Spent (Rs.)", 992,       162, "r"),
    ]

    draw.rounded_rectangle([PAD, ty, W - PAD, ty + TABLE_HEAD], radius=8, fill=NAVY)
    hy = ty + (TABLE_HEAD - 22) // 2
    for lbl, cx, cw_, align in cols:
        if   align == "c":
            center_text(draw, lbl, cx + cw_ // 2, hy, F_HEADER, WHITE)
        elif align == "r":
            draw.text((cx + cw_ - tw(draw, lbl, F_HEADER) - 10, hy), lbl, font=F_HEADER, fill=WHITE)
        else:
            draw.text((cx, hy), lbl, font=F_HEADER, fill=WHITE)

    for idx, row in enumerate(campaigns):
        ry  = ty + TABLE_HEAD + idx * TABLE_ROW
        bg  = WHITE if idx % 2 == 0 else ROW_ALT
        draw.rectangle([PAD + 1, ry, W - PAD - 1, ry + TABLE_ROW], fill=bg)
        draw.line([PAD + 1, ry, W - PAD - 1, ry], fill=BORDER, width=1)
        vy = ry + (TABLE_ROW - 20) // 2

        if row.get('is_awareness'):
            result_val = f"{row['reach']:,}"
            cpl_val    = "-"
            result_clr = NAVY
        else:
            result_val = str(row['leads'])
            cpl_val    = f"Rs. {row['cpl']:.2f}"
            result_clr = GREEN

        row_data = [
            (str(idx + 1),              "c", TEXT_MID),
            (row["campaign_name"],      "l", NAVY),
            (result_val,               "c", result_clr),
            (cpl_val,                  "c", ORANGE),
            (f"{row['ctr']}%",          "c", GREEN),
            (f"Rs. {row['spent']:.2f}", "r", ORANGE),
        ]

        for (val, align, color), (_, cx, cw_, _) in zip(row_data, cols):
            if align == "c":
                center_text(draw, val, cx + cw_ // 2, vy, F_NORMAL, color)
            elif align == "r":
                draw.text((cx + cw_ - tw(draw, val, F_NORMAL) - 10, vy), val, font=F_NORMAL, fill=color)
            else:
                for li, line in enumerate(wrap_px(draw, val, F_NORMAL, cw_ - 8)[:2]):
                    draw.text((cx, vy + li * 22), line, font=F_NORMAL, fill=color)

    if not campaigns:
        center_text(draw, "No campaign data for this date", W // 2, ty + TABLE_HEAD + 18, F_NORMAL, TEXT_MID)

    # Footer
    fy = ty + TABLE_H + GAP
    draw.rectangle([0, fy, W, fy + FOOTER_H], fill=NAVY)
    tagline = "Empowering Your Digital Growth, 100 Times Over."
    draw.text((PAD, fy + (FOOTER_H - 18) // 2), tagline, font=F_BRAND, fill=WHITE)
    site = "www.the100x.digital"
    draw.text((W - PAD - tw(draw, site, F_BRAND), fy + (FOOTER_H - 18) // 2), site, font=F_BRAND, fill=ORANGE)
    draw.rectangle([0, fy + FOOTER_H - 5, W, fy + FOOTER_H], fill=ORANGE)

    filename = f"reports/{account_name}_{report_date}.jpg"
    img.save(filename, quality=95)
    print(f"  Report saved: {filename}")
    return filename

# =============================================================
#  CLOUDINARY UPLOAD
# =============================================================

def upload_to_cloudinary(filepath):
    url = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/image/upload"
    with open(filepath, 'rb') as f:
        response = requests.post(
            url,
            files={'file': f},
            data={'upload_preset': UPLOAD_PRESET},
            verify=False
        )
    result = response.json()
    print(f"  Cloudinary status: {response.status_code}")
    image_url = result.get("secure_url")
    if image_url:
        return image_url
    raise Exception(f"Cloudinary upload failed: {result}")

# =============================================================
#  SEND WHATSAPP IMAGE
# =============================================================

def send_whatsapp_image(report_date, account_name, image_url):
    payload = {
        "to"      : PHONE_NUMBER,
        "type"    : "template",
        "template": {
            "language"  : {"policy": "deterministic", "code": "en"},
            "name"      : TEMPLATE_NAME,
            "components": [
                {
                    "type"      : "header",
                    "parameters": [
                        {"type": "image", "image": {"link": image_url}}
                    ]
                },
                {
                    "type"      : "body",
                    "parameters": [
                        {"type": "text", "text": report_date},
                        {"type": "text", "text": account_name},
                    ]
                }
            ]
        }
    }
    # Try Bearer header auth first (askeva.io preferred method)
    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type" : "application/json"
        },
        json=payload,
        verify=False
    )
    print(f"  WhatsApp status={response.status_code} (Bearer)")

    # If Bearer fails, fall back to ?token= query param
    if response.status_code not in (200, 201):
        print(f"  Bearer response: {response.text[:200]}")
        print(f"  Retrying with ?token= query param...")
        response = requests.post(
            f"{API_URL}?token={API_TOKEN}",
            headers={"Content-Type": "application/json"},
            json=payload,
            verify=False
        )
        print(f"  WhatsApp status={response.status_code} (token param)")
        if response.status_code not in (200, 201):
            print(f"  Token param response: {response.text[:200]}")

    return response.status_code in (200, 201)

# =============================================================
#  MAIN LOOP
# =============================================================

success_count = 0
fail_count    = 0
skip_count    = 0

for account_name, account_id in AD_ACCOUNTS.items():

    # Skip placeholder Tristar until ID is filled in
    if "XXXXXXXXXX" in account_id:
        print(f"\n  SKIPPING {account_name} — account ID not set")
        skip_count += 1
        continue

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
        total_reach = 0
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
            else:
                total_reach += reach
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

        print(f"  Leads={total_leads} | Reach={total_reach} | "
              f"Spent=Rs.{total_spent:.2f} | Avg CPL=Rs.{avg_cpl:.2f}")

        # Generate image
        image_path = create_report_image(
            account_name, yesterday, campaigns,
            total_leads, total_spent, avg_cpl, balance, total_reach
        )

        # Upload to Cloudinary
        image_url = upload_to_cloudinary(image_path)
        print(f"  Image URL: {image_url}")

        # Send via WhatsApp
        sent = send_whatsapp_image(yesterday, account_name, image_url)

        if sent:
            print(f"  SUCCESS: Sent for {account_name}")
            success_count += 1
        else:
            print(f"  FAILED: Not sent for {account_name}")
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
