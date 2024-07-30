import json
import os
from typing import Dict, List
import yt_dlp
import re

class Song:
    def __init__(self, author: str, streamLink: str, title: str, id: str):
        self.__author = author
        self.__streamLink = streamLink
        self.__title = title
        self.__id = id

    def getAuthor(self) -> str:
        return self.__author
    
    def getStreamLink(self) -> str:
        return self.__streamLink
    
    def getTitle(self) -> str:
        return self.__title
    
    def getId(self) -> str:
        return self.__id
    
    def to_dict(self)-> Dict[str, str]:
        return {
            'author': self.__author,
            'id': self.__id,
            'title': self.__title,
            'streamLink': self.__streamLink
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Song':
        return cls(
            author=data['author'],
            streamLink=data['streamLink'],
            title=data['title'],
            id=data['id']
        )
    
class Playlist:
    def __init__(self, name: str, songs: List[Song], id: str):
        self.__songs = songs
        self.__name = name
        self.__id = id

    def get_songs(self) -> List[Song]:
        return self.__songs
    
    def get_name(self) -> str:
        return self.__name
    
    def get_id(self) -> str:
        return self.__id
    
    def add_song(self, song: Song):
        self.__songs.append(song)

    def add_songs(self, songs: List[Song]):
        self.__songs.extend(songs)
    
    def contains_song(self, id_to_check: str) -> bool:
        doesContainId = False
        for song in self.get_songs():
            if song.getId() == id_to_check:
                doesContainId = True
                break
        return doesContainId
    
    def to_dict(self):
        return {
            'name': self.__name,
            'id': self.__id,
            'songs': [song.to_dict() for song in self.get_songs()]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'Playlist':
        songs = [Song.from_dict(song_data) for song_data in data['songs']]
        return cls(
            name=data['name'],
            id=data['id'],
            songs=songs)
    
class Radio:
    def __init__(self, playlists: List[Playlist]):
        self.__playlists = playlists

    def get_playlists(self) -> List[Playlist]:
        return self.__playlists
    
    def add_playlist(self, playlist: Playlist):
        self.__playlists.append(playlist)

    def to_dict(self):
        return {
            'playlists': [playlist.to_dict() for playlist in self.get_playlists()]
        }
    
    def get_playlist(self, playlist_id_to_get: str)-> Playlist:
        for playlist in self.get_playlists():
            if playlist.get_id() == playlist_id_to_get:
                return playlist
    
    def contains_playlist(self, playlist_id_to_check: str)-> bool:
        contains_playlist: bool = False
        for playlist in self.get_playlists():
            if playlist.get_id() == playlist_id_to_check:
                contains_playlist = True
        return contains_playlist
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'Radio':
        playlists: List[Playlist] = [Playlist.from_dict(playlist_data) for playlist_data in data['playlists']]
        return cls(
            playlists=playlists)
    
def save_radio_to_json(radio: Radio, filename: str):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(radio.to_dict(), f, indent=4)
        print(f"Radio data saved to Music/radio.json")
    except (TypeError, ValueError) as e:
        print(f"Error saving to JSON: {e}")

def load_radio_from_json(filename: str) -> Radio:
    try:
        # Open the JSON file and load its contents
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert the JSON data to a Radio object
        if 'playlists' in data:
            return Radio.from_dict(data)
        else:
            print("No 'playlists' key found in the JSON file.")
            return Radio([])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Probably empty json, returning empty Radio obj : {e}")
        return Radio([])
    
def sanitize_filename(filename):
    return re.sub(r'[^a-zA-Z0-9]', '', filename)
    
def download_song(video_url: str, output_folder, output_folder_name, output_format='m4a') -> Song :
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
        song = Song(channel_name, streamLink, unsanitized_video_title, video_id)

        ydl_opts['outtmpl'] = os.path.join(output_folder, f'{sanitized_video_title}{video_id}.%(ext)s')

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        return song

def create_folder_for_playlist(sanitized_playlist_title):
    # Sanitize the playlist title for the folder name
    playlist_folder = os.path.join(os.getcwd(), 'ZCByteVault/Music/playlists', sanitized_playlist_title)
    os.makedirs(playlist_folder, exist_ok=True)
    return playlist_folder
    
def download_playlist(playlist_url: str, radio: Radio):
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)

        playlist_id = info.get('id', 'unknown_id')
        print(f"Playlist ID: {playlist_id}")
        playlist_title = info.get('title', 'unknown playlist')
        sanitized_playlist_title = sanitize_filename(playlist_title)

        temp_playlist: Playlist = Playlist(playlist_title, [], playlist_id)

        if radio.contains_playlist(temp_playlist.get_id()):
            temp_playlist = radio.get_playlist(temp_playlist.get_id())
        else:
            radio.add_playlist(temp_playlist)

        output_folder = create_folder_for_playlist(sanitized_playlist_title)
        
        song_list = []
        for entry in info.get('entries', []):
            if not temp_playlist.contains_song(entry['id']):
                video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                song = download_song(video_url, output_folder, sanitized_playlist_title)
                song_list.append(song)
        temp_playlist.add_songs(song_list)
    

if __name__ == "__main__":
    radio_json_path: str = "ZCByteVault/Music/playlists/radio.json"
    radio: Radio
    radio = load_radio_from_json(radio_json_path)

    playlist_urls: str = input("Enter the playlist URLs (Seperated by space): ").split(" ")
    for playlist_url in playlist_urls:
        download_playlist(playlist_url, radio)

        print(radio.to_dict())
        
    
    
    save_radio_to_json(radio, radio_json_path)

