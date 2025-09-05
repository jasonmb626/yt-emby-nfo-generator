"""
given a youtube playlist id generate <playlist_id>.json and <playlist_id>.csv files
The json file will contain links to the highest resolution images for the channel and the playlist thumbails
The csv file will contain a pipe separated list of everything needed to generate .nfo files for the videos.
"""

import requests
import sys
import os
import csv
import json

YT_API_KEY = os.environ["YT_API_KEY"]
if len(sys.argv) < 3:
    print("Error: Missing commandline arg")
    sys.exit(1)

playlist_id = sys.argv[1]
out_base_path = sys.argv[2]


def save_image(url: str, outfile_path: str):
    img_data = requests.get(url).content
    with open(outfile_path, "wb") as handler:
        handler.write(img_data)


playlist_id = sys.argv[1]


def get_largest_thumbnail_url(thumbnails):
    largest_size_name = ""
    largest_size_size = 0
    for size_name in thumbnails.keys():
        width = thumbnails[size_name]["width"]
        height = thumbnails[size_name]["height"]
        overall_size = width * height
        if overall_size > largest_size_size:
            largest_size_size = overall_size
            largest_size_name = size_name
    if largest_size_name != "":
        return thumbnails[largest_size_name]["url"]
    else:
        return None


def get_channel_data(channel_id: str):
    BASE_URL = f"https://www.googleapis.com/youtube/v3/channels"
    payload = {"part": "snippet", "id": channel_id, "key": YT_API_KEY}

    res = requests.get(BASE_URL, params=payload)
    channel_data = res.json()["items"][0]["snippet"]
    user_name = channel_data["title"]
    channel_thumbnail_url = get_largest_thumbnail_url(channel_data["thumbnails"])
    return {"user_name": user_name, "channel_thumbnail_url": channel_thumbnail_url}


def get_playlist_items(playlist_id: str):
    BASE_URL = f"https://www.googleapis.com/youtube/v3/playlistItems"
    payload = {"part": "snippet", "playlistId": playlist_id, "key": YT_API_KEY}
    res = requests.get(BASE_URL, params=payload)
    items = []
    while res.status_code == 200:
        playlist_data = res.json()
        for playlist_item in playlist_data["items"]:
            channel_id = playlist_item["snippet"]["channelId"]
            video_id = playlist_item["snippet"]["resourceId"]["videoId"]
            video_title = playlist_item["snippet"]["title"]
            position = playlist_item["snippet"]["position"]
            items.append(
                {
                    "channel_id": channel_id,
                    "video_id": video_id,
                    "playlist_index": position + 1,
                    "video_title": video_title,
                }
            )
        if "nextPageToken" not in playlist_data:
            break
        payload["pageToken"] = playlist_data["nextPageToken"]
        res = requests.get(BASE_URL, params=payload)
    return items


def get_playlist_info(channel_id: str, playlist_id: str):
    BASE_URL = f"https://www.googleapis.com/youtube/v3/playlists"
    payload = {"part": "snippet", "channelId": channel_id, "key": YT_API_KEY}
    all_playlists = []
    res = requests.get(BASE_URL, params=payload)
    while res.status_code == 200:
        channel_playlist_data = res.json()
        for playlist in channel_playlist_data["items"]:
            id = playlist["id"]
            title = playlist["snippet"]["title"]
            published_at = playlist["snippet"]["publishedAt"]
            thumbnails = playlist["snippet"]["thumbnails"]
            all_playlists.append(
                {
                    "id": id,
                    "title": title,
                    "published_at": published_at,
                    "thumbnails": thumbnails,
                }
            )
        if "nextPageToken" not in channel_playlist_data:
            break
        payload["pageToken"] = channel_playlist_data["nextPageToken"]
        res = requests.get(BASE_URL, params=payload)
    all_playlists.sort(key=lambda x: x["published_at"])
    playlist_nbr = -1
    for i in range(len(all_playlists)):
        if all_playlists[i]["id"] == playlist_id:
            playlist_nbr = i
            break
    if playlist_nbr >= 0:
        id = all_playlists[playlist_nbr]["id"]
        title = all_playlists[playlist_nbr]["title"]
        thumbnail_url = get_largest_thumbnail_url(
            all_playlists[playlist_nbr]["thumbnails"]
        )
        return {
            "playlist_id": id,
            "title": title,
            "thumbnail_url": thumbnail_url,
            "playlist_nbr": playlist_nbr,
        }
    return None


raw_playlist_items = get_playlist_items(playlist_id)
channel_id = raw_playlist_items[0]["channel_id"]
if channel_id is None:
    print("Error: Unable to determine channel id. Exiting.")
    sys.exit(2)

playlist_items = []
for playlist_item in raw_playlist_items:
    playlist_index = playlist_item["playlist_index"]
    video_id = playlist_item["video_id"]
    video_title = playlist_item["video_title"]
    new_item = {
        "playlist_index": playlist_index,
        "video_id": video_id,
        "video_title": video_title,
    }
    playlist_items.append(new_item)

channel_info = get_channel_data(channel_id)
playlist_info = get_playlist_info(channel_id, playlist_id)
user_name = channel_info["user_name"]
playlist_name = playlist_info["title"]
season_nbr = playlist_info["playlist_nbr"] + 1
playlist_data = {
    "channel_name": user_name,
    "playlist_name": playlist_name,
    "channel_thumbnail_url": channel_info["channel_thumbnail_url"],
    "playlist_thumbnail_url": playlist_info["thumbnail_url"],
    "playlist_id": playlist_id,
    "playlist_nbr": playlist_info["playlist_nbr"],
}
channel_out_path = os.path.join(out_base_path, playlist_data["channel_name"])
playlist_out_path = os.path.join(channel_out_path, f"Season {season_nbr:03d}")
if not os.path.exists(playlist_out_path):
    os.makedirs(playlist_out_path)
with open(os.path.join(playlist_out_path, "dl_playlist.sh"), "w") as txt_file:
    txt_file.write(
        f"""yt-dlp -o "%(playlist_index)s - %(id)s - %(title)s.%(ext)s" \\
--sleep-interval 5 \\
--max-sleep-interval 15 \\
--retries infinite \\
--fragment-retries infinite \\
--concurrent-fragments 3 \\
--compat-options filename-sanitization \\
--extractor-args "youtube:player_client=default,-tv" \\
-f "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]" \\
--merge-output-format mp4 "https://www.youtube.com/playlist?list={playlist_id}"
"""
    )
with open(os.path.join(playlist_out_path, "playlist.json"), "w") as json_file:
    json.dump(playlist_data, json_file)
with open(os.path.join(playlist_out_path, "playlist.csv"), "w") as csv_file:
    writer = csv.DictWriter(
        csv_file,
        delimiter="|",
        fieldnames=["playlist_index", "video_id", "video_title"],
    )
    writer.writeheader()
    writer.writerows(playlist_items)

out_playlist_thumbnail_path = os.path.join(
    channel_out_path, f"season{season_nbr:02d}-poster.jpg"
)
if not os.path.exists(os.path.join(channel_out_path, "poster.jpg")):
    save_image(
        playlist_data["channel_thumbnail_url"],
        os.path.join(channel_out_path, "poster.jpg"),
    )
save_image(
    playlist_data["playlist_thumbnail_url"],
    os.path.join(channel_out_path, out_playlist_thumbnail_path),
)
