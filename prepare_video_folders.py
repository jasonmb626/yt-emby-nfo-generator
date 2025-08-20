import requests
import json
import sys
import os


def save_image(url: str, outfile_path: str):
    img_data = requests.get(url).content
    with open(outfile_path, "wb") as handler:
        handler.write(img_data)


out_base_path = sys.argv[1]
playlist_id = sys.argv[2]
json_file_path = playlist_id + ".json"

if not os.path.exists(json_file_path):
    print("Error: " + json_file_path + " does not exist")
    sys.exit(1)

with open(json_file_path, "r") as json_file:
    playlist_data = json.load(json_file)
season_nbr = playlist_data["playlist_nbr"]

out_path = os.path.join(out_base_path, playlist_data["channel_name"])
if not os.path.exists(out_path):
    os.makedirs(out_path)

out_playlist_thumbnail_path = os.path.join(
    out_path, f"season{season_nbr:02d}-poster.jpg"
)
if not os.path.exists(os.path.join(out_path, "poster.jpg")):
    save_image(
        playlist_data["channel_thumbnail_url"], os.path.join(out_path, "poster.jpg")
    )
save_image(
    playlist_data["playlist_thumbnail_url"],
    os.path.join(out_path, out_playlist_thumbnail_path),
)
