import requests
import sys
import os
import json

YT_API_KEY = os.environ['YT_API_KEY']
CHANNEL_ID = 'UCFAooJDn9izFea2JpAp8vUQ'
PLAYLIST_ID = 'PLz4NmdSG1VFsneupYtKgU-DrdhcJIDbp1'

def get_largest_thumbnail_url(thumbnails):
    largest_size_name = ''
    largest_size_size = 0
    for size_name in thumbnails.keys():
        width = thumbnails[size_name]['width']
        height = thumbnails[size_name]['height']
        overall_size = width * height
        if overall_size > largest_size_size:
            largest_size_size = overall_size
            largest_size_name = size_name
    if largest_size_name != '':
        return thumbnails[largest_size_name]['url']
    else:
        return None

def get_channel_data(channel_id: str):
    BASE_URL = f"https://www.googleapis.com/youtube/v3/channels"
    payload = {
        'part': 'snippet',
        'id': channel_id,
        'key': YT_API_KEY
    }

    res = requests.get(BASE_URL, params=payload)
    channel_data = res.json()['items'][0]['snippet']
    user_name = channel_data['title']
    channel_thumbnail_url = get_largest_thumbnail_url(channel_data['thumbnails'])
    return {
        'user_name': user_name,
        'channel_thumbnail_url': channel_thumbnail_url
    }

def get_playlist_items(playlist_id: str):
    BASE_URL = f"https://www.googleapis.com/youtube/v3/playlistItems"
    payload = {
        'part': 'snippet',
        'playlistId': playlist_id,
        'key': YT_API_KEY
    }
    res = requests.get(BASE_URL, params=payload)
    items = []
    while res.status_code == 200:
        playlist_data = res.json()
        for playlist_item in playlist_data['items']:
            channel_id = playlist_item['snippet']['channelId']
            video_id = playlist_item['snippet']['resourceId']['videoId']
            video_title = playlist_item['snippet']['title']
            items.append({
                'channel_id': channel_id,
                'video_id': video_id,
                'video_title': video_title
            })
        if 'nextPageToken' not in playlist_data:
            break
        payload['pageToken'] = playlist_data['nextPageToken']
        res = requests.get(BASE_URL, params=payload)
    return items

def get_playlist_info(channel_id: str, playlist_id: str):
    BASE_URL = f"https://www.googleapis.com/youtube/v3/playlists"
    payload = {
        'part': 'snippet',
        'channelId': channel_id,
        'key': YT_API_KEY
    }
    res = requests.get(BASE_URL, params=payload)
    while res.status_code == 200:
        channel_playlist_data = res.json()
        for playlist in channel_playlist_data['items']:
            if playlist['id'] == playlist_id:
                id = playlist['id']
                title = playlist['snippet']['title']
                thumbnail_url = get_largest_thumbnail_url(playlist['snippet']['thumbnails'])
                return {
                    'playlist_id': id,
                    'title': title,
                    'thumbnail_url': thumbnail_url
                }
        if 'nextPageToken' not in channel_playlist_data:
            break
        payload['pageToken'] = channel_playlist_data['nextPageToken']
        res = requests.get(BASE_URL, params=payload)
    return None

playlist_items = get_playlist_items(PLAYLIST_ID)
channel_id = playlist_items[0]['channel_id']
if channel_id is not None:
    playlist_info = get_playlist_info(channel_id, PLAYLIST_ID)
    playlist_info['items'] = playlist_items
    playlist_info['channel_info'] = get_channel_data(channel_id)
print (playlist_info)
