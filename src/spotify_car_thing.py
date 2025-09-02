from flask import Flask, render_template_string

# Initialize Flask
app = Flask(__name__)

# LCD HTML template
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
        .header { background: black; color: white; padding: 4px 8px; text-align: center;
            font-size: 9px; font-weight: 500; border-bottom: 1px solid #333; }
        .album-art-container { flex: 1; display: flex; align-items: center; justify-content: center;
            padding: 12px; background: black; }
        .album-art { width: 110px; height: 110px; border-radius: 4px; object-fit: cover;
            border: 1px solid #333; }
        .track-info { padding: 8px 12px; text-align: center; background: black;
            border-top: 1px solid #333; min-height: 50px; }
        .track-title { font-size: 11px; font-weight: 600; margin-bottom: 3px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: white; }
        .track-artist { font-size: 9px; color: #999; margin-bottom: 6px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .progress-bar { width: 100%; height: 2px; background: #333; border-radius: 1px;
            overflow: hidden; margin: 4px 0; }
        .progress-fill { height: 100%; background: white; width: 0%; transition: width 1s linear; }
        .time-info { display: flex; justify-content: space-between; font-size: 7px;
            color: #666; margin-bottom: 4px; }
        .controls { display: flex; justify-content: center; align-items: center;
            gap: 16px; padding: 8px; background: black; border-top: 1px solid #333; }
        .control-btn { background: black; border: 1px solid #555; color: white;
            cursor: pointer; padding: 6px; border-radius: 50%; transition: all 0.2s;
            display: flex; align-items: center; justify-content: center; }
        .control-btn:hover { background: #222; border-color: #777; }
        .control-btn:active { background: #333; }
        .play-pause-btn { width: 32px; height: 32px; background: white; color: black;
            border: 1px solid white; font-size: 12px; }
        .play-pause-btn:hover { background: #ddd; }
        .prev-next-btn { width: 28px; height: 28px; font-size: 10px; }
        .status-indicator { position: absolute; top: 6px; right: 6px; width: 4px; height: 4px;
            border-radius: 50%; background: white; }
        .no-track { display: flex; flex-direction: column; align-items: center;
            justify-content: center; height: 100%; color: #666; }
        .no-track-icon { font-size: 20px; margin-bottom: 6px; }
        .no-track-text { font-size: 9px; text-align: center; }
    </style>
</head>

<body>
    <div class="status-indicator"></div>
    <div class="header">SPOTIFY</div>

    <div id="player-content">
        <div class="no-track">
            <div class="no-track-icon">♫</div>
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

            if (!trackData) {
                content.innerHTML = `
                    <div class="no-track">
                        <div class="no-track-icon">♫</div>
                        <div class="no-track-text">No track playing</div>
                    </div>`;
                return;
            }

            content.innerHTML = `
                <div class="album-art-container">
                    <img src="${trackData.albumArt}" alt="Album Art" class="album-art"
                        onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22 viewBox=%220 0 120 120%22><rect width=%22120%22 height=%22120%22 fill=%22%23333%22/><text x=%2260%22 y=%2260%22 text-anchor=%22middle%22 fill=%22white%22 font-size=%2212%22>♫</text></svg>'">
                </div>
                <div class="track-info">
                    <div class="track-title">${trackData.title}</div>
                    <div class="track-artist">${trackData.artist}</div>
                    <div class="time-info">
                        <span>${formatTime(progress)}</span>
                        <span>${formatTime(duration)}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${(progress/duration)*100}%"></div>
                    </div>
                </div>
                <div class="controls">
                    <button class="control-btn prev-next-btn" onclick="previousTrack()">⏮</button>
                    <button class="control-btn play-pause-btn" onclick="togglePlayPause()">
                        ${isPlaying ? '⏸' : '▶'}
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
            isPlaying = !isPlaying;
            fetch('/api/play-pause', { method: 'POST' });
            updateDisplay(currentTrack);
        }
        function nextTrack() { fetch('/api/next', { method: 'POST' }); }
        function previousTrack() { fetch('/api/previous', { method: 'POST' }); }

        setInterval(() => {
            if (isPlaying && currentTrack) {
                progress += 1;
                if (progress >= duration) { progress = 0; }
                updateDisplay(currentTrack);
            }
        }, 1000);

        setInterval(async() => {
            try {
                const response = await fetch('/api/current-track');
                const data = await response.json();
                if (data.track) {
                    currentTrack = data.track;
                    isPlaying = data.is_playing;
                    progress = data.progress;
                    duration = data.duration;
                    updateDisplay(currentTrack);
                }
            } catch (error) { console.error('Error fetching track data:', error); }
        }, 5000);

        setTimeout(() => {
            currentTrack = {
                title: "Sample Song Title That Might Be Long",
                artist: "Sample Artist Name",
                albumArt: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='110' height='110' viewBox='0 0 110 110'><rect width='110' height='110' fill='%23222' stroke='%23555'/><text x='55' y='55' text-anchor='middle' fill='%23999' font-size='12'>♫</text></svg>"
            };
            isPlaying = true;
            progress = 45;
            duration = 180;
            updateDisplay(currentTrack);
        }, 2000);
    </script>
</body>
</html>
"""

# ------------------- Flask Routes -------------------

@app.route('/lcd')
def lcd_display():
    return LCD_HTML

@app.route('/api/current-track')
def api_current_track():
    if not spotify_client:
        return {"error": "Spotify not initialized"}, 500

    track_data = spotify_client.get_current_track()
    if not track_data or not track_data.get('track_name'):
        return {"track": None, "is_playing": False, "progress": 0, "duration": 0}

    return {
        "track": {
            "title": track_data['track_name'],
            "artist": track_data['artist_string'],
            "albumArt": track_data['album_art_url'] or "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='110' height='110' viewBox='0 0 110 110'><rect width='110' height='110' fill='%23222' stroke='%23555'/><text x='55' y='55' text-anchor='middle' fill='%23999' font-size='12'>♫</text></svg>"
        },
        "is_playing": track_data['is_playing'],
        "progress": track_data['progress_ms'] // 1000,  # ✅ comma fixed here
        "duration": track_data['duration_ms'] // 1000
    }

@app.route('/api/play-pause', methods=['POST'])
def api_play_pause():
    if not spotify_client:
        return {"error": "Spotify not initialized"}, 500
    return {"success": spotify_client.play_pause()}

@app.route('/api/next', methods=['POST'])
def api_next():
    if not spotify_client:
        return {"error": "Spotify not initialized"}, 500
    return {"success": spotify_client.next_track()}

@app.route('/api/previous', methods=['POST'])
def api_previous():
    if not spotify_client:
        return {"error": "Spotify not initialized"}, 500
    return {"success": spotify_client.previous_track()}

# ------------------- Run Flask -------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
