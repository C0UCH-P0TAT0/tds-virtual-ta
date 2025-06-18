import requests
from datetime import datetime, timezone
import time
import os
import json
from bs4 import BeautifulSoup

# Paste your valid `_t` cookie here (DO NOT decode or change it)
SESSION_COOKIE = "kekjyH4JIScIRob%2ByFL3sShB%2FiAalEKU%2F%2Bv%2Bv%2FuPM66EdlYb0aZMavmim7vqNGxJlKg3X8A%2F9JJ5YBFVxmDM2uWACGZy9YXs%2FLrYSqF0ueUisjsRYQMDN7O6GuMSLA87S6T9z0tcV1qJ852dzaVoZHGdvbiA2LDLf6fi1t9KbIxz82iE0aiY41HsSSJ4wvqu5%2BFKXUwMNOgOL7A1a2Lc%2FcoxV0%2FFxRMF2J2QHn%2FbGMj2jSmss3wdNPsXrC%2Fud4LMO8flWlqNaKCNuVAlKV92O1G%2BZkS1SZfrSARqnHw5kVU%2BXRMFhLk2nPplYtqsFFKbZt7JfQ%3D%3D--WroyNsPvcLu3fFyl--YC7WJuAk%2BRyyLzBj31uETQ%3D%3D"

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
                posts = post_json.get("post_stream", {}).get("posts", [])
                
                all_text = []
                all_html = []

                for post in posts:
                    html = post.get("cooked", "")
                    soup = BeautifulSoup(html, "html.parser")
                    text = soup.get_text(separator="\n").strip()
                    all_text.append(text)
                    all_html.append(html)

                content_text = "\n\n---\n\n".join(all_text)
                content_html = "\n\n<hr/>\n\n".join(all_html)

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