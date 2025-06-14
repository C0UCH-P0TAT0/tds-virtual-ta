import requests
from datetime import datetime, timezone
import time
import os
import json
from bs4 import BeautifulSoup

# Paste your valid `_t` cookie here (DO NOT decode or change it)
SESSION_COOKIE = "1VZD4hjcklRGcDOdH%2BkfWGRhVIf0embZI1OuDnsRlI753Oz8EhrV1131PbMn5yQ%2FxZ%2BbdWmH0gd8kYal%2FsmFzK8B3yvPhZ7DxmNq14MwwoAaPH8p13hyPRUHVq6D7RrdHpYB414qVPFl1F01Gw%2BWtg%2FKAR7w7OJcih8hfF0kVuVH1XLmpLhYDR66w4GPwHgiJ37Y%2FHT43ID%2F7%2Bsc1rX8DKWCBiyCgafW8on1hGA4EZq1vcUHb2Xg1UI8pVG4gP%2Be%2BS%2BNTNrvmKDU16vdCCIZNOgJAVCtYjUsXokhT444hnJAGO5x9MM4Mmkvq9BtREuH6kS6Wg%3D%3D--3zM2thc8s9G7%2BUBZ--uw6%2BAxqMgnNB6DGg%2FcVgyw%3D%3D"

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_URL = f"{BASE_URL}/c/courses/tds-kb/34.json"

# Date range for filtering posts
DATE_FROM = datetime(2025, 1, 1, tzinfo=timezone.utc)
DATE_TO = datetime(2025, 4, 14, tzinfo=timezone.utc)

# Auth cookies + headers
cookies = {"_t": SESSION_COOKIE}
headers = {"User-Agent": "Mozilla/5.0"}

# Check login
login_check = requests.get(f"{BASE_URL}/session/current.json", headers=headers, cookies=cookies)
try:
    user_data = login_check.json()
    if user_data.get("current_user") is None:
        print("❌ Not logged in. Check your session cookie.")
        exit()
    else:
        print(f"✅ Logged in as: {user_data['current_user']['username']}")
except Exception as e:
    print("❌ Login check failed:", e)
    exit()

# Begin scraping
all_topics = []
page = 1
empty_streak = 0
MAX_EMPTY_STREAK = 3

while True:
    url = CATEGORY_URL.replace('.json', f'.json?page={page}')
    print(f"📄 Fetching: {url}")
    r = requests.get(url, headers=headers, cookies=cookies)

    try:
        data = r.json()
    except Exception as e:
        print("❌ JSON parse error:", e)
        print("Response:\n", r.text[:500])
        break

    topics = data.get("topic_list", {}).get("topics", [])
    if not topics:
        break

    matches = 0
    for topic in topics:
        created = datetime.fromisoformat(topic["created_at"].replace("Z", "+00:00"))
        if created < DATE_FROM:
            continue
        if DATE_FROM <= created <= DATE_TO:
            topic_url = f"{BASE_URL}/t/{topic['slug']}/{topic['id']}.json"
            try:
                post_r = requests.get(topic_url, headers=headers, cookies=cookies)
                post_json = post_r.json()
                first_post = post_json.get("post_stream", {}).get("posts", [])[0]
                content_html = first_post.get("cooked", "")

                # Parse and clean HTML to extract readable text
                soup = BeautifulSoup(content_html, "html.parser")
                content_text = soup.get_text(separator="\n").strip()

            except Exception as e:
                print(f"⚠️ Failed to fetch or parse content for topic ID {topic['id']}: {e}")
                content_html = ""
                content_text = ""

            topic_data = {
                "id": topic["id"],
                "title": topic["title"],
                "created_at": topic["created_at"],
                "url": f"{BASE_URL}/t/{topic['slug']}/{topic['id']}",
                "content_html": content_html,
                "content_text": content_text
            }
            all_topics.append(topic_data)
            matches += 1

    if matches == 0:
        empty_streak += 1
        print(f"⚠️ Page {page}: 0 matches (empty streak = {empty_streak})")
        if empty_streak >= MAX_EMPTY_STREAK:
            print("📉 No matches for 3 pages. Stopping.")
            break
    else:
        print(f"✅ Page {page}: {matches} matching topics.")
        empty_streak = 0

    page += 1
    time.sleep(1)

# Save results
save_path = "tds_virtual_ta/data/discourse"
os.makedirs(save_path, exist_ok=True)
filename = os.path.join(save_path, "jan2025_posts.json")

with open(filename, "w", encoding="utf-8") as f:
    json.dump(all_topics, f, indent=2)

print(f"\n💾 Saved {len(all_topics)} topics to: {filename}\n")

# Sample print
print("📌 Sample Questions:")
for t in all_topics[:5]:
    print(f"- {t['title']} ({t['created_at']})")
    print(f"  {t['content_text'][:100]}...")
