"""
Minimal Spotify Display Flask App
Start here to test basic functionality
"""

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import sys
import os
import threading
import time

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

def update_track_data():
    """Background thread to update track data"""
    global current_track
    while True:
        if spotify_client:
            try:
                track_data = spotify_client.get_current_track()
                current_track = track_data
                if track_data.get('is_playing'):
                    print(f"🎵 {track_data.get('track_name')} - {track_data.get('artist_string')}")
            except Exception as e:
                print(f"Error updating track data: {e}")
        time.sleep(3)

# API Routes
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

# Main display route
@app.route('/')
def index():
    """Simple test display"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Spotify Display Test</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: #191414; 
                color: white; 
                text-align: center;
                padding: 50px;
            }
            .container { max-width: 400px; margin: 0 auto; }
            .track { font-size: 24px; margin: 20px 0; }
            .artist { font-size: 18px; color: #1db954; }
            .status { font-size: 14px; opacity: 0.7; margin-top: 30px; }
            .loading { opacity: 0.5; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 Spotify Display</h1>
            <div id="track-info" class="loading">
                <div class="track">Loading...</div>
                <div class="artist">Connecting to Spotify</div>
            </div>
            <div class="status" id="status">Starting up...</div>
        </div>
        
        <script>
            function updateDisplay() {
                fetch('/api/current-track')
                    .then(response => response.json())
                    .then(data => {
                        const trackInfo = document.getElementById('track-info');
                        const status = document.getElementById('status');
                        
                        if (data.is_playing && data.track_name) {
                            trackInfo.innerHTML = `
                                <div class="track">${data.track_name}</div>
                                <div class="artist">${data.artist_string}</div>
                            `;
                            trackInfo.classList.remove('loading');
                            status.textContent = 'Playing ♪';
                        } else {
                            trackInfo.innerHTML = `
                                <div class="track">No track playing</div>
                                <div class="artist">Start playing something on Spotify</div>
                            `;
                            trackInfo.classList.add('loading');
                            status.textContent = 'Not playing';
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        document.getElementById('status').textContent = 'Connection error';
                    });
            }
            
            // Update every 3 seconds
            setInterval(updateDisplay, 3000);
            updateDisplay(); // Initial load
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

if __name__ == '__main__':
    print("🚀 Starting Spotify Display...")
    
    # Initialize Spotify
    if not init_spotify():
        print("❌ Failed to start. Check your .env file.")
        sys.exit(1)
    
    # Start background thread
    thread = threading.Thread(target=update_track_data, daemon=True)
    thread.start()
    
    # Load config
    config = load_config()
    
    print(f"🌐 Open: http://localhost:{config.FLASK_PORT}")
    print("🎧 Start playing music on Spotify to see it appear!")
    
    # Start Flask
    app.run(host='0.0.0.0', port=config.FLASK_PORT, debug=config.DEBUG)