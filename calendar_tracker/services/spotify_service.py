import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

class SpotifyService:
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:5000/callback')
        
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Spotify credentials not found in environment variables")
            
        self.scope = " ".join([
            "streaming",
            "user-read-email",
            "user-read-private",
            "user-modify-playback-state",
            "user-read-playback-state",
            "user-read-currently-playing"
        ])
        
        self.sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        )
        
    def get_auth_url(self):
        """Get Spotify authorization URL"""
        return self.sp_oauth.get_authorize_url()
        
    def get_token(self, code):
        """Get token from authorization code"""
        return self.sp_oauth.get_access_token(code, as_dict=True)
        
    def get_client(self, token):
        """Get Spotify client with token"""
        return spotipy.Spotify(auth=token)
        
    def get_current_playback(self, sp):
        """Get current playback state"""
        try:
            playback = sp.current_playback()
            if not playback:
                return None
                
            return {
                'is_playing': playback['is_playing'],
                'item': {
                    'name': playback['item']['name'],
                    'artist': playback['item']['artists'][0]['name'],
                    'duration': playback['item']['duration_ms'],
                    'progress': playback['progress_ms']
                } if playback['item'] else None
            }
        except Exception as e:
            print(f"Error getting playback: {str(e)}")
            return None
            
    def control_playback(self, sp, action, device_id=None):
        """Control playback (play/pause/next/previous)"""
        try:
            if action == 'play':
                sp.start_playback(device_id=device_id)
            elif action == 'pause':
                sp.pause_playback(device_id=device_id)
            elif action == 'next':
                sp.next_track(device_id=device_id)
            elif action == 'previous':
                sp.previous_track(device_id=device_id)
            return True
        except Exception as e:
            print(f"Error controlling playback: {str(e)}")
            return False
            
    def set_volume(self, sp, volume_percent):
        """Set playback volume"""
        try:
            sp.volume(volume_percent)
            return True
        except Exception as e:
            print(f"Error setting volume: {str(e)}")
            return False
