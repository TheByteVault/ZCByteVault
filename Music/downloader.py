import json
import os
import yt_dlp
import re

class Song:
    def __init__(self, author, streamLink, title, source):
        self.author = author
        self.streamLink = streamLink
        self.title = title
        self.source = source

    def description(self):
        return f"{self.author}, {self.streamLink}, {self.title}, {self.source}"
    
    def to_dict(self):
        return {
            'author': self.author,
            'source': self.source,
            'title': self.title,
            'streamLink': self.streamLink
        }
    
class Playlist:
    def __init__(self, name, songs):
        self.songs = songs
        self.name = name

    def get_songs(self):
        return self.songs
    
    def to_dict(self):
        return {
            'name': self.name,
            'songs': [song.to_dict() for song in self.songs]
        }

def sanitize_filename(filename):
    return re.sub(r'[^a-zA-Z0-9]', '', filename)

def create_folder_for_playlist(sanitized_playlist_title):
    # Sanitize the playlist title for the folder name
    playlist_folder = os.path.join(os.getcwd(), 'playlists', sanitized_playlist_title)
    os.makedirs(playlist_folder, exist_ok=True)
    return playlist_folder

def download_audio(video_url, output_folder, output_folder_name, output_format='m4a'):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': output_format,
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)

        unsanitized_video_title = info.get('title', 'unknown')
        sanitized_video_title = sanitize_filename(info.get('title', 'unknown'))
        channel_name = info.get('uploader', 'unknown')
        video_id = sanitize_filename(info.get('id', 'unknown'))  # This video id will be used to append to the song, just so the song title is always unique

        streamLink = f'https://github.com/TheByteVault/ZCByteVault/raw/main/Music/playlists/{output_folder_name}/{sanitized_video_title}{video_id}.m4a'
        song = Song(channel_name, streamLink, unsanitized_video_title, video_url)
        print(song.description())

        ydl_opts['outtmpl'] = os.path.join(output_folder, f'{sanitized_video_title}{video_id}.%(ext)s')

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        return song

def download_playlist(playlist_url):
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        playlist_title = info.get('title', 'unknown playlist')
        sanitized_playlist_title = sanitize_filename(playlist_title)
        output_folder = create_folder_for_playlist(sanitized_playlist_title)
        song_list = []
        for entry in info.get('entries', []):
            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
            song = download_audio(video_url, output_folder, sanitized_playlist_title)
            song_list.append(song)
        playlist_obj = Playlist(playlist_title, song_list)
    return playlist_obj

def save_playlists_to_json(playlists, filename):
    playlists_data = [playlist.to_dict() for playlist in playlists]
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(playlists_data, f, indent=4)
        print(f"Playlists data saved to {filename}")
    except (TypeError, ValueError) as e:
        print(f"Error saving to JSON: {e}")

if __name__ == "__main__":
    playlists = []
    playlist_urls = input("Enter the playlist URLs (Seperated by space): ").split(" ")
    for playlist_url in playlist_urls:
        playlist = download_playlist(playlist_url)
        playlists.append(playlist)
    # Path to save JSON file
    json_filename = os.path.join(os.getcwd(), 'playlists', 'playlists_data.json')

    # Save playlists to JSON
    save_playlists_to_json(playlists, json_filename)