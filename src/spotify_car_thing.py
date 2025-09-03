# spotify_lcd_display.py
"""
Complete Spotify LCD Display
Integrates your LCD design with your existing Spotify client
"""

from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
import sys
import os
import threading
import time
import requests
from io import BytesIO
import base64

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_loader import load_config
from spotify_client import SpotifyClient

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Global variables
spotify_client = None
current_track = {}
cached_album_art = {}

def init_spotify():
    """Initialize Spotify client"""
    global spotify_client
    try:
        config = load_config()
        spotify_client = SpotifyClient(
            config.SPOTIFY_CLIENT_ID,
            config.SPOTIFY_CLIENT_SECRET,
            config.SPOTIFY_REDIRECT_URI
        )
        print("✅ Spotify client initialized")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize Spotify: {e}")
        return False

def download_and_cache_album_art(url, track_id):
    """Download and cache album art as base64"""
    global cached_album_art
    
    if track_id in cached_album_art:
        return cached_album_art[track_id]
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            img_str = base64.b64encode(response.content).decode()
            encoded_art = f"data:image/jpeg;base64,{img_str}"
            cached_album_art[track_id] = encoded_art
            
            # Keep cache reasonable size
            if len(cached_album_art) > 15:
                oldest_key = next(iter(cached_album_art))
                del cached_album_art[oldest_key]
            
            return encoded_art
    except Exception as e:
        print(f"Error downloading album art: {e}")
    return None

def update_track_data():
    """Background thread to update track data"""
    global current_track
    while True:
        if spotify_client:
            try:
                track_data = spotify_client.get_current_track()
                
                if track_data and track_data.get('album_art_url') and track_data.get('track_id'):
                    album_art_base64 = download_and_cache_album_art(
                        track_data['album_art_url'], 
                        track_data['track_id']
                    )
                    if album_art_base64:
                        track_data['album_art_base64'] = album_art_base64
                
                current_track = track_data or {}
                
                if track_data and track_data.get('is_playing'):
                    print(f"🎵 {track_data.get('track_name')} - {track_data.get('artist_string')}")
            except Exception as e:
                print(f"Error updating track data: {e}")
                current_track = {}
        time.sleep(2)

# LCD HTML Template
LCD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=230, height=320, initial-scale=1.0">
    <title>Spotify LCD Display</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: black; color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            width: 230px; height: 320px; overflow: hidden;
            display: flex; flex-direction: column;
        }
        .header { 
            background: black; color: white; padding: 4px 8px; text-align: center;
            font-size: 9px; font-weight: 500; border-bottom: 1px solid #333; 
        }
        .album-art-container { 
            flex: 1; display: flex; align-items: center; justify-content: center;
            padding: 12px; background: black; 
        }
        .album-art { 
            width: 110px; height: 110px; border-radius: 4px; object-fit: cover;
            border: 1px solid #333; 
        }
        .track-info { 
            padding: 8px 12px; text-align: center; background: black;
            border-top: 1px solid #333; min-height: 50px; 
        }
        .track-title { 
            font-size: 11px; font-weight: 600; margin-bottom: 3px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: white; 
        }
        .track-artist { 
            font-size: 9px; color: #999; margin-bottom: 6px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
        }
        .progress-bar { 
            width: 100%; height: 2px; background: #333; border-radius: 1px;
            overflow: hidden; margin: 4px 0; 
        }
        .progress-fill { 
            height: 100%; background: white; width: 0%; transition: width 1s linear; 
        }
        .time-info { 
            display: flex; justify-content: space-between; font-size: 7px;
            color: #666; margin-bottom: 4px; 
        }
        .controls { 
            display: flex; justify-content: center; align-items: center;
            gap: 16px; padding: 8px; background: black; border-top: 1px solid #333; 
        }
        .control-btn { 
            background: black; border: 1px solid #555; color: white;
            cursor: pointer; padding: 6px; border-radius: 50%; transition: all 0.2s;
            display: flex; align-items: center; justify-content: center; 
        }
        .control-btn:hover { background: #222; border-color: #777; }
        .control-btn:active { background: #333; }
        .play-pause-btn { 
            width: 32px; height: 32px; background: white; color: black;
            border: 1px solid white; font-size: 12px; 
        }
        .play-pause-btn:hover { background: #ddd; }
        .prev-next-btn { width: 28px; height: 28px; font-size: 10px; }
        .status-indicator { 
            position: absolute; top: 6px; right: 6px; width: 4px; height: 4px;
            border-radius: 50%; background: white; 
        }
        .no-track { 
            display: flex; flex-direction: column; align-items: center;
            justify-content: center; height: 100%; color: #666; 
        }
        .no-track-icon { font-size: 20px; margin-bottom: 6px; }
        .no-track-text { font-size: 9px; text-align: center; }
        .loading { animation: pulse 2s infinite; }
        @keyframes pulse {
            0% { opacity: 0.5; }
            50% { opacity: 1; }
            100% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="status-indicator" id="statusIndicator"></div>
    <div class="header">SPOTIFY</div>

    <div id="player-content">
        <div class="no-track">
            <div class="no-track-icon loading">♫</div>
            <div class="no-track-text">Connecting to Spotify...</div>
        </div>
    </div>

    <script>
        let currentTrack = null;
        let isPlaying = false;
        let progress = 0;
        let duration = 0;

        function updateDisplay(trackData) {
            const content = document.getElementById('player-content');
            const statusIndicator = document.getElementById('statusIndicator');

            if (!trackData || !trackData.track_name) {
                content.innerHTML = `
                    <div class="no-track">
                        <div class="no-track-icon">♫</div>
                        <div class="no-track-text">No track playing</div>
                    </div>`;
                statusIndicator.style.background = '#666';
                return;
            }

            statusIndicator.style.background = trackData.is_playing ? '#1db954' : '#666';
            
            const albumArt = trackData.album_art_base64 || 
                "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='110' height='110' viewBox='0 0 110 110'><rect width='110' height='110' fill='%23222' stroke='%23555'/><text x='55' y='55' text-anchor='middle' fill='%23999' font-size='12'>♫</text></svg>";

            content.innerHTML = `
                <div class="album-art-container">
                    <img src="${albumArt}" alt="Album Art" class="album-art"
                        onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22110%22 height=%22110%22 viewBox=%220 0 110 110%22><rect width=%22110%22 height=%22110%22 fill=%22%23333%22/><text x=%2255%22 y=%2255%22 text-anchor=%22middle%22 fill=%22white%22 font-size=%2212%22>♫</text></svg>'">
                </div>
                <div class="track-info">
                    <div class="track-title">${trackData.track_name}</div>
                    <div class="track-artist">${trackData.artist_string}</div>
                    <div class="time-info">
                        <span>${formatTime(trackData.progress_ms / 1000)}</span>
                        <span>${formatTime(trackData.duration_ms / 1000)}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${(trackData.progress_ms/trackData.duration_ms)*100}%"></div>
                    </div>
                </div>
                <div class="controls">
                    <button class="control-btn prev-next-btn" onclick="previousTrack()">⏮</button>
                    <button class="control-btn play-pause-btn" onclick="togglePlayPause()">
                        ${trackData.is_playing ? '⏸' : '▶'}
                    </button>
                    <button class="control-btn prev-next-btn" onclick="nextTrack()">⏭</button>
                </div>`;
        }

        function formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }

        function togglePlayPause() {
            fetch('/api/play-pause', { method: 'POST' })
                .then(response => response.json())
                .then(data => console.log('Play/pause:', data))
                .catch(error => console.error('Error:', error));
        }
        
        function nextTrack() { 
            fetch('/api/next', { method: 'POST' })
                .then(response => response.json())
                .then(data => console.log('Next track:', data))
                .catch(error => console.error('Error:', error));
        }
        
        function previousTrack() { 
            fetch('/api/previous', { method: 'POST' })
                .then(response => response.json())
                .then(data => console.log('Previous track:', data))
                .catch(error => console.error('Error:', error));
        }

        // Fetch current track data
        async function fetchTrackData() {
            try {
                const response = await fetch('/api/current-track');
                const data = await response.json();
                updateDisplay(data);
            } catch (error) { 
                console.error('Error fetching track data:', error);
                updateDisplay(null);
            }
        }

        // Update every 2 seconds
        setInterval(fetchTrackData, 2000);
        fetchTrackData(); // Initial load
    </script>
</body>
</html>
"""

# Flask Routes
@app.route('/')
def index():
    return render_template_string(LCD_HTML)

@app.route('/lcd')
def lcd_display():
    return render_template_string(LCD_HTML)

@app.route('/api/current-track')
def api_current_track():
    """Get current track info"""
    return jsonify(current_track)

@app.route('/api/status')
def api_status():
    """Get app status"""
    return jsonify({
        'spotify_connected': spotify_client is not None,
        'has_track_data': bool(current_track),
        'is_playing': current_track.get('is_playing', False)
    })

@app.route('/api/play-pause', methods=['POST'])
def api_play_pause():
    """Toggle play/pause"""
    if not spotify_client:
        return {"error": "Spotify not initialized"}, 500
    
    try:
        # Check if currently playing
        track_data = spotify_client.get_current_track()
        if track_data and track_data.get('is_playing'):
            # Pause
            response = requests.put(
                'https://api.spotify.com/v1/me/player/pause',
                headers={'Authorization': f'Bearer {spotify_client.access_token}'}
            )
        else:
            # Play
            response = requests.put(
                'https://api.spotify.com/v1/me/player/play',
                headers={'Authorization': f'Bearer {spotify_client.access_token}'}
            )
        
        return {"success": response.status_code in [200, 204]}
    except Exception as e:
        print(f"Error with play/pause: {e}")
        return {"error": str(e)}, 500

@app.route('/api/next', methods=['POST'])
def api_next():
    """Skip to next track"""
    if not spotify_client:
        return {"error": "Spotify not initialized"}, 500
    
    try:
        response = requests.post(
            'https://api.spotify.com/v1/me/player/next',
            headers={'Authorization': f'Bearer {spotify_client.access_token}'}
        )
        return {"success": response.status_code in [200, 204]}
    except Exception as e:
        print(f"Error skipping to next: {e}")
        return {"error": str(e)}, 500

@app.route('/api/previous', methods=['POST'])
def api_previous():
    """Skip to previous track"""
    if not spotify_client:
        return {"error": "Spotify not initialized"}, 500
    
    try:
        response = requests.post(
            'https://api.spotify.com/v1/me/player/previous',
            headers={'Authorization': f'Bearer {spotify_client.access_token}'}
        )
        return {"success": response.status_code in [200, 204]}
    except Exception as e:
        print(f"Error skipping to previous: {e}")
        return {"error": str(e)}, 500

if __name__ == '__main__':
    print("🚀 Starting Spotify LCD Display...")
    
    # Initialize Spotify
    if not init_spotify():
        print("❌ Failed to start. Check your .env file.")
        sys.exit(1)
    
    # Start background thread
    thread = threading.Thread(target=update_track_data, daemon=True)
    thread.start()
    
    # Load config
    config = load_config()
    
    print(f"🌐 LCD Display: http://localhost:{config.FLASK_PORT}")
    print("🎧 Start playing music on Spotify to see it appear!")
    print("💡 Open the URL and display it on your LCD monitor")
    
    # Start Flask
    app.run(host='0.0.0.0', port=config.FLASK_PORT, debug=config.DEBUG)