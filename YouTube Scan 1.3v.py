from datetime import datetime, date, timedelta, timezone
import requests
import isodate



API_KEY = 
CHANNEL_ID = 

# Thailand timezone
TH_TZ = timezone(timedelta(hours=7))

# Schedule (HH, MM)
SCHEDULE = [
    (7, 0),
    (9, 0),
    (10, 0),
    (12, 0),
    (14, 0),
    (15, 0),
    (16, 0),
    (18, 0),
    (20, 0),
]

TOLERANCE_MINUTES = 60


# Date range
START_DATE = date(2026, 3, 2)   # change year if needed

# ================= HELPERS =================

def parse_duration(duration_iso):
    return int(isodate.parse_duration(duration_iso).total_seconds())


def get_videos_for_date(target_date):
    published_after = datetime.combine(
        target_date, datetime.min.time(), tzinfo=TH_TZ
    ).astimezone(timezone.utc)


    published_before = published_after + timedelta(days=1)

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": API_KEY,
        "channelId": CHANNEL_ID,
        "part": "snippet",
        "type": "video",
        "order": "date",
        "maxResults": 50,
        "publishedAfter": published_after.isoformat(),
        "publishedBefore": published_before.isoformat(),
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("items", [])


def get_video_details(video_id):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "key": API_KEY,
        "id": video_id,
        "part": "contentDetails",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    items = response.json().get("items", [])
    return items[0] if items else None

# ================= MAIN =================

def main():
    end_date = datetime.now(TH_TZ).date()
    current_date = START_DATE

    print("==== YouTube Upload Schedule Check ====")
    print(f"Range: {START_DATE.strftime('%d %b')} → {end_date.strftime('%d %b')}")
    print()

    while current_date <= end_date:
        print("=" * 45)
        print("Date:", current_date.strftime("%d %b"))
        print()

        videos = get_videos_for_date(current_date)
        found_any = False

        for item in videos:
            snippet = item["snippet"]
            video_id = item["id"]["videoId"]

            published_utc = datetime.fromisoformat(
                snippet["publishedAt"].replace("Z", "+00:00")
            )
            published_local = published_utc.astimezone(TH_TZ)

            details = get_video_details(video_id)
            if not details:
                continue

            duration_iso = details["contentDetails"]["duration"]
            duration_seconds = parse_duration(duration_iso)

            video_type = "Short (duration-based)" if duration_seconds <= 90 else "Long Video"

            print("Title        :", snippet["title"])
            print("Published at :✅ ", published_local.strftime("%H:%M:%S"))
            print("Date         :", published_local.strftime("%d %b"))
            print("Duration     :", f"{duration_seconds}s")
            print("Type         :", video_type)

            matched = False

            for hour, minute in SCHEDULE:
                expected_time = published_local.replace(
                    hour=hour,
                    minute=minute,
                    second=0,
                    microsecond=0
                )

                diff_minutes = (published_local - expected_time).total_seconds() / 60

                if 0 <= diff_minutes <= TOLERANCE_MINUTES:
                    print(f"Matched      : ✅ {hour:02d}:{minute:02d}")
                    matched = True
                    break

            if not matched:
                print("Matched      : ❌ No schedule match")

            print("-" * 45)
            found_any = True

        if not found_any:
            print("❌ No uploads found for this day")

        current_date += timedelta(days=1)

    print("\nDone.")
    input("Press ENTER to exit")

# ================= RUN =================

if __name__ == "__main__":
    main()
