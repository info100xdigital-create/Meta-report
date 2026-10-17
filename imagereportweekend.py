import os
import requests
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

# =============================================================
#  CONFIGURATION  — edit only this section
# =============================================================

ACCESS_TOKEN  = "EAAXt5oeongwBSgvZANANfzqGJRWLCAkvwZCsaKgRZAKbZCFKH2DolRLfiTF6pgQFPjHpWdJ1B7JX803fvDjH51iUfh0sSEH1XWCyZCSAnfDDby4CbPMIZCOCMllezKMy0urJYvOVvDFHvSYzFncAgZB5FUcdj4x2dNslRsLgQaZCPp8kUNSe4ZBwMGup3p5UxvvGvahbBmDG4XLYgCbvu2rNb6x0RXT0Wubfy7pqhZBVSoMkyS2BDo17c6soOPCmrFUxT9EOM9xA5jccstoYTFYHbkh8cR"
APP_ID        = "1668949257788940"
APP_SECRET    = "a08dd86d56c0f3ce2fa3b5fe9c36c905"

API_URL       = "https://accounts.100xflow.com/v1/message/send-message"
API_TOKEN     = "4833c7160371e93c91ea9845e14308887ab62a57441e079d51fa799f8985f2679e8839394b655bbaf49eaba0d4d2d877d6885cfa6d3966b4dd4921300de9434d"
PHONE_NUMBER  = "919360363056"
TEMPLATE_NAME = "scheduled_meta_ads_report_image"

CLOUD_NAME    = "dfcmienp8"
UPLOAD_PRESET = "ml_default"

# ── Logo: your file is "Logo.png" (capital L) in the project folder ──
# The script tries all variants automatically — just keep Logo.png in
# the same folder as this script.
LOGO_CANDIDATES = ["Logo.png", "logo.png", "logo.PNG", "logo.jpg", "logo.jpeg", "LOGO.PNG"]

AD_ACCOUNTS = {
    "ICFix Academy"        : "act_1039999246750750",
    "VLCC Chrompet"        : "act_1454865038899929",
    "Sri Balaji"           : "act_2019953192089948",
    "Maneesh Dentistry"    : "act_1226766042198241",
    "Shine Family Clinic"  : "act_1661111898449106",
    "MS Dental"            : "act_756150509871499",
    "AMPPA"                : "act_1492447055881532",
    "MCubeAcademy"         : "act_2039104906883816",
    "Easa Garden"          : "act_4386371744960663",
    "Genora Global Studies": "act_1617073839583401",
    "Barath Avenue"        : "act_1382301152911804",
    "Bling Detailing"      : "act_545109656842741",
}

# =============================================================
#  INIT
# =============================================================

FacebookAdsApi.init(APP_ID, APP_SECRET, ACCESS_TOKEN)
FacebookAdsApi.get_default_api().SDK_VERSION = "v25.0"

# =============================================================
#  DATE LOGIC — WEEKEND REPORT
#  Always fetches Saturday + Sunday combined
#  Run this file every Monday morning
# =============================================================

today      = datetime.now()
date_since = (today - timedelta(days=2)).strftime('%Y-%m-%d')  # Saturday
date_until = (today - timedelta(days=1)).strftime('%Y-%m-%d')  # Sunday
report_label = f"Weekend: {date_since} to {date_until}"
yesterday  = date_since  # kept for backward compatibility
print(f"\n{'='*55}")
print(f"  META ADS WEEKEND REPORT  |  Sat + Sun: {date_since} to {date_until}")
print(f"{'='*55}\n")

os.makedirs("reports", exist_ok=True)

# =============================================================
#  FONTS
#  Tries Windows Arial first, then Linux Liberation / DejaVu.
#  Works on both Windows and Linux servers.
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
    """Pixel width of a text string."""
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]

def center_text(draw, text, cx, y, font, fill):
    draw.text((cx - tw(draw, text, font) // 2, y), text, font=font, fill=fill)

def wrap_px(draw, text, font, max_w):
    """Word-wrap to fit within max_w pixels. Returns list of lines."""
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
#  LOGO DRAWING
#  - Draws white pill background unconditionally (always visible)
#  - Tries every candidate filename to load the real logo
#  - Falls back to clean branded text if no file found
# =============================================================

def draw_logo(img, draw, x, y, LW=195, LH=74):
    # Step 1: white rounded background — always drawn first
    draw.rounded_rectangle([x, y, x + LW, y + LH], radius=10, fill=WHITE)

    # Step 2: try to load real logo file
    for path in LOGO_CANDIDATES:
        if os.path.exists(path):
            try:
                logo = Image.open(path).convert("RGBA")
                logo.thumbnail((LW - 16, LH - 12), Image.LANCZOS)

                # Composite logo onto a white base so transparency is preserved
                base = Image.new("RGBA", (LW, LH), (255, 255, 255, 255))
                paste_x = (LW - logo.width)  // 2
                paste_y = (LH - logo.height) // 2
                base.paste(logo, (paste_x, paste_y), logo)
                img.paste(base.convert("RGB"), (x, y))

                print(f"  Logo loaded: {path}  ({logo.width}x{logo.height}px)")
                return
            except Exception as e:
                print(f"  Logo load error ({path}): {e}")

    # Step 3: text fallback — always looks professional
    draw.text((x + 12, y + 6),        "The",       font=F_LOGO_S, fill=TEXT_MID)
    draw.text((x + 12, y + 22),       "100",       font=F_LOGO_B, fill=NAVY)
    x2 = x + 12 + tw(draw, "100", F_LOGO_B)
    draw.text((x2,     y + 22),       "X",         font=F_LOGO_B, fill=ORANGE)
    draw.text((x + 12, y + LH - 20),  ".Digital",  font=F_LOGO_S, fill=TEXT_MID)
    print("  Logo: text fallback  (Logo.png not found in script folder)")

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

def get_ad_account_balance(account_id):
    """
    Parses Available Balance from funding_source_details.display_string.
    FundingSourceDetails is an SDK object — access via fsd['key'] not fsd.get().
    e.g. "Available balance (Rs.2,922.68 INR)" -> 2922.68
    """
    try:
        data = AdAccount(account_id).api_get(
            fields=['funding_source_details', 'balance']
        )
        fsd = data.get('funding_source_details')

        # SDK object — use bracket access, not .get()
        if fsd is not None:
            try:
                import re as _re
                display = fsd['display_string']
                if display:
                    match = _re.search(r'[\d,]+\.?\d*', display)
                    if match:
                        val = round(float(match.group().replace(',', '')), 2)
                        print(f"  Balance: Rs. {val:.2f}")
                        return val
            except Exception as e:
                print(f"  Balance display_string error: {e}")

        # Fallback: balance field (paise) -> rupees
        raw = float(data.get('balance', 0))
        val = round(raw / 100, 2)
        print(f"  Balance fallback: Rs. {val:.2f}")
        return val

    except Exception as e:
        print(f"  Balance Error: {e}")
        return 0.0


def create_report_image(account_name, report_date, campaigns,
                        total_leads, total_spent, avg_cpl, balance, total_reach=0):

    # ── Canvas dimensions ────────────────────────────────────
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

    # ── 1. HEADER ────────────────────────────────────────────
    draw.rectangle([0, 0, W, HEADER_H], fill=NAVY)

    draw.text((PAD, 26), "THE 100X.DIGITAL", font=F_TITLE, fill=WHITE)
    dx = PAD + tw(draw, "THE 100X.DIGITAL", F_TITLE) + 16
    draw.text((dx, 26), "-  META ADS REPORT", font=F_TITLE, fill=ORANGE)

    # Logo — white pill on right side of header
    LW, LH = 195, 74
    lx = W - PAD - LW
    ly = (HEADER_H - LH) // 2
    draw_logo(img, draw, lx, ly, LW, LH)

    # Orange accent bottom line
    draw.rectangle([0, HEADER_H - 5, W, HEADER_H], fill=ORANGE)

    # ── 2. META INFO STRIP ───────────────────────────────────
    my = HEADER_H
    draw.rectangle([0, my, W, my + META_H], fill=WHITE)
    draw.line([0, my + META_H - 1, W, my + META_H - 1], fill=BORDER, width=1)
    py = my + 17

    def pill(x, w, label, value, bg, lc, vc, bc=BORDER):
        draw.rounded_rectangle([x, py, x + w, py + 54],
                                radius=8, fill=bg, outline=bc, width=1)
        draw.text((x + 14, py + 9),  label, font=F_SMALL, fill=lc)
        draw.text((x + 14, py + 30), value, font=F_BRAND,  fill=vc)

    pill(PAD,       216, "Date",    report_date,   LIGHT_BG, TEXT_MID, NAVY)
    pill(PAD + 232, 290, "Account", account_name,  LIGHT_BG, TEXT_MID, NAVY)

    # Available Balance pill — auto-width based on text
    bal_text  = f"Rs. {balance:.2f}"
    bal_label = "Available Balance"
    bal_tw    = tw(draw, bal_text,  F_HEADER)
    lbl_tw    = tw(draw, bal_label, F_SMALL)
    bpw       = max(bal_tw, lbl_tw) + 36   # padding on both sides
    bpx       = W - PAD - bpw
    # Orange border ring + navy fill
    draw.rounded_rectangle([bpx - 3, py - 3, bpx + bpw + 3, py + 57], radius=10, fill=ORANGE)
    draw.rounded_rectangle([bpx,     py,     bpx + bpw,     py + 54], radius=8,  fill=NAVY)
    # Label centred
    lbl_x = bpx + (bpw - lbl_tw) // 2
    draw.text((lbl_x, py + 7),  bal_label, font=F_SMALL,  fill=(200, 210, 255))
    # Value centred
    val_x = bpx + (bpw - bal_tw) // 2
    draw.text((val_x, py + 27), bal_text,  font=F_HEADER, fill=ORANGE)

    # ── 3. SUMMARY STAT CARDS ────────────────────────────────
    sy = my + META_H + GAP
    cw = (W - 2 * PAD - 2 * GAP) // 3

    # If the account has zero leads but has reach (all campaigns are
    # awareness-only), show Total Reach instead of Total Leads so the
    # card never just displays a meaningless 0.
    if total_leads > 0:
        first_card = ("Total Leads", str(total_leads), GREEN)
    elif total_reach > 0:
        first_card = ("Total Reach", f"{total_reach:,}", GREEN)
    else:
        first_card = ("Total Leads", str(total_leads), GREEN)

    cards = [
        first_card,
        ("Amount Spent",     f"Rs. {total_spent:.2f}",  ORANGE),
        ("Avg. Cost / Lead", f"Rs. {avg_cpl:.2f}",   NAVY),
    ]

    for i, (label, value, accent) in enumerate(cards):
        cx = PAD + i * (cw + GAP)
        # Shadow
        draw.rounded_rectangle([cx + 3, sy + 3, cx + cw + 3, sy + STATS_H + 3],
                                radius=14, fill=SHADOW)
        # Card
        draw.rounded_rectangle([cx,     sy,     cx + cw,     sy + STATS_H],
                                radius=14, fill=WHITE)
        # Colour top stripe
        draw.rounded_rectangle([cx, sy, cx + cw, sy + 8], radius=0, fill=accent)
        # Text
        draw.text((cx + 20, sy + 22), label, font=F_SMALL, fill=TEXT_MID)
        draw.text((cx + 20, sy + 60), value, font=F_VALUE, fill=accent)

    # ── 4. CAMPAIGN TABLE ────────────────────────────────────
    ty = sy + STATS_H + GAP

    # Section label + underline
    draw.text((PAD, ty + 6), "Campaign Performance", font=F_HEADER, fill=NAVY)
    uw = tw(draw, "Campaign Performance", F_HEADER)
    draw.line([PAD, ty + LABEL_H - 4, PAD + uw, ty + LABEL_H - 4],
              fill=ORANGE, width=3)
    ty += LABEL_H + GAP // 2

    # Table card (shadow + white)
    draw.rounded_rectangle([PAD - 2, ty - 2, W - PAD + 2, ty + TABLE_H + 2],
                            radius=10, fill=SHADOW)
    draw.rounded_rectangle([PAD,     ty,     W - PAD,     ty + TABLE_H],
                            radius=10, fill=WHITE)

    # Column layout: (header label, x_start, col_width, alignment)
    cols = [
        ("#",           PAD + 10,  34,  "c"),
        ("Campaign",    PAD + 56,  448, "l"),
        ("Results",     624,        90, "c"),
        ("CPL (Rs.)",   730,       142, "c"),
        ("CTR %",       888,        90, "c"),
        ("Spent (Rs.)", 992,       162, "r"),
    ]

    # Header row (navy)
    draw.rounded_rectangle([PAD, ty, W - PAD, ty + TABLE_HEAD],
                            radius=8, fill=NAVY)
    hy = ty + (TABLE_HEAD - 22) // 2
    for lbl, cx, cw_, align in cols:
        if   align == "c":
            center_text(draw, lbl, cx + cw_ // 2, hy, F_HEADER, WHITE)
        elif align == "r":
            draw.text((cx + cw_ - tw(draw, lbl, F_HEADER) - 10, hy),
                      lbl, font=F_HEADER, fill=WHITE)
        else:
            draw.text((cx, hy), lbl, font=F_HEADER, fill=WHITE)

    # Data rows
    for idx, row in enumerate(campaigns):
        ry  = ty + TABLE_HEAD + idx * TABLE_ROW
        bg  = WHITE if idx % 2 == 0 else ROW_ALT
        draw.rectangle([PAD + 1, ry, W - PAD - 1, ry + TABLE_ROW], fill=bg)
        draw.line([PAD + 1, ry, W - PAD - 1, ry], fill=BORDER, width=1)
        vy = ry + (TABLE_ROW - 20) // 2

        # Awareness: show Reach in Results col, "-" in CPL col
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

        for (val, align, color), (lbl_, cx, cw_, _) in zip(row_data, cols):
            if align == "c":
                center_text(draw, val, cx + cw_ // 2, vy, F_NORMAL, color)
            elif align == "r":
                draw.text((cx + cw_ - tw(draw, val, F_NORMAL) - 10, vy),
                          val, font=F_NORMAL, fill=color)
            else:
                # Wrap long campaign names to 2 lines max
                for li, line in enumerate(wrap_px(draw, val, F_NORMAL, cw_ - 8)[:2]):
                    draw.text((cx, vy + li * 22), line, font=F_NORMAL, fill=color)

    # No data message
    if not campaigns:
        center_text(draw, "No campaign data for this date",
                    W // 2, ty + TABLE_HEAD + 18, F_NORMAL, TEXT_MID)

    # ── 5. FOOTER ────────────────────────────────────────────
    fy = ty + TABLE_H + GAP
    draw.rectangle([0, fy, W, fy + FOOTER_H], fill=NAVY)

    tagline = "Empowering Your Digital Growth, 100 Times Over."
    draw.text((PAD, fy + (FOOTER_H - 18) // 2), tagline, font=F_BRAND, fill=WHITE)

    site = "www.the100x.digital"
    draw.text((W - PAD - tw(draw, site, F_BRAND), fy + (FOOTER_H - 18) // 2),
              site, font=F_BRAND, fill=ORANGE)

    draw.rectangle([0, fy + FOOTER_H - 5, W, fy + FOOTER_H], fill=ORANGE)

    # ── Save ─────────────────────────────────────────────────
    filename = f"reports/{account_name}_Weekend_{date_since}_to_{date_until}.jpg"
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
            data={'upload_preset': UPLOAD_PRESET}
        )
    result = response.json()
    print(f"  Cloudinary status: {response.status_code}")
    image_url = result.get("secure_url")
    if image_url:
        return image_url
    raise Exception(f"Cloudinary upload failed: {result}")

# =============================================================
#  SEND WHATSAPP
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
    response = requests.post(f"{API_URL}?token={API_TOKEN}", json=payload)
    print(f"  WhatsApp status={response.status_code}  |  {response.text}")

# =============================================================
#  MAIN LOOP
# =============================================================

for account_name, account_id in AD_ACCOUNTS.items():

    print(f"Processing: {account_name}  ({account_id})")

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
        print(f"  Campaigns fetched: {len(insights_data)}")

        if not insights_data:
            print(f"  No spend data for {account_name} on {yesterday}")
            continue

        campaigns   = []
        total_leads = 0
        total_reach = 0
        total_spent = 0.0

        # Awareness objectives — show Reach instead of Leads/CPL
        # Pure awareness only — CTWA/Engagement/Leads show Results
        AWARENESS_OBJECTIVES = {
            'BRAND_AWARENESS', 'REACH', 'VIDEO_VIEWS',
            'PAGE_LIKES', 'EVENT_RESPONSES',
            'OUTCOME_AWARENESS',
        }

        # Only match awareness by name if it explicitly says awareness/reach
        # Do NOT include engagement/CTWA/video as awareness
        AWARENESS_NAME_KEYWORDS = [
            'awareness', 'brand awareness', 'reach campaign'
        ]

        for item in insights_data:
            spend     = round(float(item.get('spend', 0)), 2)
            objective = item.get('objective', '').upper()
            camp_name = item.get('campaign_name', '').lower()
            is_aware  = (
                objective in AWARENESS_OBJECTIVES or
                any(kw in camp_name for kw in AWARENESS_NAME_KEYWORDS)
            )
            reach     = int(item.get('reach', 0)) if is_aware else 0
            leads     = 0 if is_aware else get_leads(item.get('actions', []))
            cpl       = 0 if is_aware else get_cpl(item.get('cost_per_action_type', []))
            ctr       = get_ctr(item)

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

        avg_cpl = round(total_spent / total_leads, 2) if total_leads > 0 else 0
        balance = get_ad_account_balance(account_id)

        print(f"  Total leads={total_leads}  |  Total reach={total_reach}  |  "
              f"Spent=Rs.{total_spent:.2f}  |  "
              f"Avg CPL=Rs.{avg_cpl:.2f}")

        # Generate image
        image_path = create_report_image(
            account_name, f"{date_since} & {date_until}", campaigns,
            total_leads, total_spent, avg_cpl, balance, total_reach
        )

        # Upload to Cloudinary
        image_url = upload_to_cloudinary(image_path)
        print(f"  Image URL: {image_url}")

        # Send via WhatsApp
        send_whatsapp_image(f"{date_since} & {date_until}", account_name, image_url)

    except Exception as e:
        print(f"  ERROR for {account_name}: {e}")

print(f"\n{'='*55}")
print("  ALL REPORTS COMPLETED")
print(f"{'='*55}\n")