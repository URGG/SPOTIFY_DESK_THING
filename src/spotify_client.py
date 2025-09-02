"""
Spotify API client wrapper
Handles authentication and data fetching
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """Initialize Spotify client with credentials"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        
        # Spotify scopes needed
        self.scope = "user-read-currently-playing user-read-playback-state user-modify-playback-state"
        
        # Initialize Spotify client
        self.auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            cache_path=".spotify_cache"
        )
        
        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
        self._last_track_data = {}
        self._last_fetch_time = 0
        
    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """Get currently playing track information"""
        try:
            current_track = self.sp.current_user_playing_track()
            
            if not current_track or not current_track.get('item'):
                return self._format_no_track_response()
            
            track_data = self._format_track_data(current_track)
            self._last_track_data = track_data
            self._last_fetch_time = time.time()
            
            return track_data
            
        except Exception as e:
            logger.error(f"Error fetching current track: {e}")
            # Return last known data if available
            if self._last_track_data and (time.time() - self._last_fetch_time) < 30:
                return self._last_track_data
            return self._format_error_response(str(e))
    
    def _format_track_data(self, current_track: Dict) -> Dict[str, Any]:
        """Format raw Spotify data into clean structure"""
        item = current_track['item']
        
        # Get album art (prefer largest image)
        album_art = None
        if item['album']['images']:
            album_art = item['album']['images'][0]['url']  # First is usually largest
        
        # Get all artist names
        artists = [artist['name'] for artist in item['artists']]
        
        return {
            'is_playing': current_track['is_playing'],
            'track_name': item['name'],
            'artist_names': artists,
            'artist_string': ', '.join(artists),
            'album_name': item['album']['name'],
            'album_art_url': album_art,
            'progress_ms': current_track.get('progress_ms', 0),
            'duration_ms': item['duration_ms'],
            'track_id': item['id'],
            'external_url': item['external_urls'].get('spotify'),
            'popularity': item.get('popularity', 0),
            'explicit': item.get('explicit', False),
            'timestamp': time.time()
        }
    
    def _format_no_track_response(self) -> Dict[str, Any]:
        """Return formatted response when no track is playing"""
        return {
            'is_playing': False,
            'track_name': None,
            'artist_names': [],
            'artist_string': '',
            'album_name': None,
            'album_art_url': None,
            'progress_ms': 0,
            'duration_ms': 0,
            'track_id': None,
            'external_url': None,
            'popularity': 0,
            'explicit': False,
            'timestamp': time.time()
        }
    
    def _format_error_response(self, error_message: str) -> Dict[str, Any]:
        """Return formatted error response"""
        response = self._format_no_track_response()
        response['error'] = error_message
        return response
    
    def play_pause(self) -> bool:
        """Toggle play/pause state"""
        try:
            current = self.get_current_track()
            if current and current['is_playing']:
                self.sp.pause_playback()
            else:
                self.sp.start_playbook()
            return True
        except Exception as e:
            logger.error(f"Error toggling play/pause: {e}")
            return False
    
    def next_track(self) -> bool:
        """Skip to next track"""
        try:
            self.sp.next_track()
            return True
        except Exception as e:
            logger.error(f"Error skipping to next track: {e}")
            return False
    
    def previous_track(self) -> bool:
        """Skip to previous track"""
        try:
            self.sp.previous_track()
            return True
        except Exception as e:
            logger.error(f"Error skipping to previous track: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if client is properly authenticated"""
        try:
            # Try a simple API call to test authentication
            self.sp.current_user()
            return True
        except Exception:
            return False