import csv
import sys
import os
import glob
import json

# Assumes playlist downloaded with this command
# yt-dlp -o "%(playlist)s/%(playlist_index)s - %(id)s - %(title)s.%(ext)s" --restrict-filenames "<URL>"

SEASON_NFO_TEMPLATE = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<season>
  <plot />
  <outline />
  <lockdata>false</lockdata>
  <lockedfields>Name</lockedfields>
  <title>%TITLE%</title>
  <sorttitle>%SORT_TITLE%</sorttitle>
  <seasonnumber>%SE%</seasonnumber>
  <code>%CD%</code>
</season>"""

VIDEO_NFO_TEMPLATE = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<episodedetails>
  <lockdata>false</lockdata>
  <lockedfields>Name|SortName</lockedfields>
  <title>%TITLE%</title>
  <sorttitle>%SORT_TITLE%</sorttitle>
  <episode>%EP%</episode>
  <season>%SE%</season>
</episodedetails>"""

videos_dir = sys.argv[1]
files = glob.glob(os.path.join(videos_dir, "*.mp4"))
files.extend(glob.glob(os.path.join(videos_dir, "*.mkv")))
files.extend(glob.glob(os.path.join(videos_dir, "*.webm")))
files.sort()

json_file_path = os.path.join(videos_dir, 'playlist.json')
csv_file_path = os.path.join(videos_dir, 'playlist.csv')

if not os.path.exists(csv_file_path):
    print("Error: " + csv_file_path + " does not exist")
    sys.exit(1)

videos = []
with open(csv_file_path, "r") as csv_file:
    reader = csv.DictReader(csv_file, delimiter="|")
    for row in reader:
        videos.append(row)

if not os.path.exists(json_file_path):
    print("Error: " + json_file_path + " does not exist")
    sys.exit(1)

with open(json_file_path, "r") as json_file:
    playlist_data = json.load(json_file)
    playlist_id = playlist_data['playlist_id']
    season_nbr = playlist_data["playlist_nbr"] + 1

nfo_data = (
    SEASON_NFO_TEMPLATE.replace("%TITLE%", playlist_data["playlist_name"])
    .replace("%SORT_TITLE%", f"{season_nbr:02d} - {playlist_data['playlist_name']}")
    .replace("%SE%", str(season_nbr))
    .replace("%CD%", playlist_id)
)
with open(os.path.join(videos_dir, "season.nfo"), "w") as nfo_file:
    nfo_file.write(nfo_data)

for file in files:
    base_file = os.path.basename(file)
    if base_file.endswith(".mkv"):
        nfo_file = base_file.replace(".mkv", ".nfo")
    elif base_file.endswith(".mp4"):
        nfo_file = base_file.replace(".mp4", ".nfo")
    elif file.endswith(".webm"):
        nfo_file = base_file.replace(".webm", ".nfo")
    video_id = base_file.split(" - ")[1]
    try:
        video_data = next(iter([i for i in videos if i["video_id"] == video_id]))
    except:
        print("Couldn't find " + video_id)
        video_data = None
        continue
    playlist_index = int(video_data["playlist_index"])
    nfo_data = (
        VIDEO_NFO_TEMPLATE.replace("%TITLE%", video_data["video_title"])
        .replace("%SORT_TITLE%", f"{playlist_index:03d} - {video_data['video_title']}")
        .replace("%EP%", str(playlist_index))
        .replace("%SE%", str(season_nbr))
    )
    with open(os.path.join(videos_dir, nfo_file), "w") as nfo_file:
        nfo_file.write(nfo_data)
