import os
import time
import threading
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
from display_controller_fixed import LCDDisplayController  # Your existing display controller
from spotify_client import SpotifyClient  # Your existing Spotify client

class SpotifyCarThingUI:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height
        
        # Spotify Car Thing color scheme
        self.spotify_green = (30, 215, 96)
        self.dark_bg = (18, 18, 18)
        self.light_bg = (40, 40, 40) 
        self.card_bg = (35, 35, 35)
        self.white = (255, 255, 255)
        self.gray = (180, 180, 180)
        self.dark_gray = (120, 120, 120)
        self.accent_blue = (45, 125, 255)
        
        # Load fonts
        self.load_fonts()
        
        # Album art cache
        self.album_art_cache = {}
        
    def load_fonts(self):
        """Load fonts with fallbacks"""
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",  # Windows
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "/usr/share/fonts/truetype/arial.ttf",  # Linux
        ]
        
        try:
            # Try to find Arial font
            font_path = None
            for path in font_paths:
                if os.path.exists(path):
                    font_path = path
                    break
            
            if font_path:
                self.font_huge = ImageFont.truetype(font_path, 58)
                self.font_large = ImageFont.truetype(font_path, 42)
                self.font_medium = ImageFont.truetype(font_path, 32)
                self.font_small = ImageFont.truetype(font_path, 22)
                self.font_tiny = ImageFont.truetype(font_path, 16)
            else:
                raise Exception("No system fonts found")
                
        except Exception as e:
            print(f"⚠️ Using default fonts: {e}")
            # Fallback to default font
            default = ImageFont.load_default()
            self.font_huge = default
            self.font_large = default
            self.font_medium = default
            self.font_small = default
            self.font_tiny = default
    
    def truncate_text(self, text, font, max_width):
        """Truncate text to fit within max_width"""
        if not text:
            return ""
        
        # Try full text first
        try:
            bbox = font.getbbox(text)
            if bbox[2] <= max_width:
                return text
        except:
            # Fallback for older Pillow versions
            return text[:40]
        
        # Truncate and add ellipsis
        for i in range(len(text) - 1, 0, -1):
            truncated = text[:i] + "..."
            try:
                bbox = font.getbbox(truncated)
                if bbox[2] <= max_width:
                    return truncated
            except:
                return text[:30] + "..."
        
        return text[:10] + "..."
    
    def download_album_art(self, url, size=(250, 250)):
        """Download and cache album art"""
        if not url or url in self.album_art_cache:
            return self.album_art_cache.get(url)
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
                img = img.resize(size, Image.Resampling.LANCZOS)
                self.album_art_cache[url] = img
                return img
        except Exception as e:
            print(f"⚠️ Failed to download album art: {e}")
        
        return None
    
    def create_spotify_display(self, current_track=None, playback_state=None):
        """Create the main Spotify Car Thing display"""
        img = Image.new('RGB', (self.width, self.height), color=self.dark_bg)
        draw = ImageDraw.Draw(img)
        
        # Draw header
        self.draw_header(draw)
        
        # Check if we have track data in the right format
        if current_track and (current_track.get('track_name') or current_track.get('item')):
            # Draw now playing screen
            self.draw_now_playing_screen(draw, current_track, playback_state)
        else:
            # Draw idle screen
            self.draw_idle_screen(draw)
        
        return img
    
    def draw_header(self, draw):
        """Draw the top header bar"""
        # Header background
        draw.rectangle((0, 0, self.width, 70), fill=self.light_bg)
        
        # Spotify logo area
        logo_x = 30
        draw.ellipse((logo_x, 15, logo_x + 40, 55), fill=self.spotify_green)
        draw.text((logo_x + 10, 20), "♪", fill=self.white, font=self.font_medium)
        
        # Spotify text
        draw.text((logo_x + 60, 20), "SPOTIFY", fill=self.spotify_green, font=self.font_large)
        
        # Current time
        current_time = datetime.now().strftime("%I:%M %p")
        try:
            time_width = draw.textbbox((0, 0), current_time, font=self.font_medium)[2]
        except:
            time_width = len(current_time) * 15  # Fallback
        draw.text((self.width - time_width - 30, 22), current_time, fill=self.white, font=self.font_medium)
        
        # Connection status dot
        draw.ellipse((self.width - time_width - 60, 28, self.width - time_width - 50, 38), fill=self.spotify_green)
    
    def draw_now_playing_screen(self, draw, current_track, playback_state):
        """Draw the now playing interface"""
        # Handle both formats - direct track data or nested in 'item'
        if current_track.get('item'):
            # Spotify API format
            item = current_track['item']
            track_name = item.get('name', 'Unknown Track')
            artists = item.get('artists', [])
            album_name = item.get('album', {}).get('name', '')
            album_images = item.get('album', {}).get('images', [])
            progress_ms = current_track.get('progress_ms', 0)
            duration_ms = item.get('duration_ms', 0)
            is_playing = current_track.get('is_playing', False)
        else:
            # Our custom format
            track_name = current_track.get('track_name', 'Unknown Track')
            artist_names = current_track.get('artist_names', [])
            artists = [{'name': name} for name in artist_names] if artist_names else []
            album_name = current_track.get('album_name', '')
            album_images = [{'url': current_track.get('album_art_url')}] if current_track.get('album_art_url') else []
            progress_ms = current_track.get('progress_ms', 0)
            duration_ms = current_track.get('duration_ms', 0)
            is_playing = current_track.get('is_playing', False)
        
        # Main content area
        content_y = 90
        
        # Album art
        art_size = 240
        art_x = 60
        art_y = content_y + 20
        
        # Try to get album art
        album_art = None
        if album_images:
            art_url = album_images[0]['url'] if album_images[0].get('url') else None
            if art_url:
                album_art = self.download_album_art(art_url, (art_size, art_size))
        
        # Album art placeholder/border
        draw.rectangle((art_x, art_y, art_x + art_size, art_y + art_size), 
                      fill=self.card_bg, outline=self.gray, width=3)
        
        if album_art:
            # Paste album art (simplified for this example)
            try:
                # Create a temporary image to handle the album art
                temp_img = Image.new('RGB', (self.width, self.height), self.dark_bg)
                temp_img.paste(album_art, (art_x, art_y))
                # For now, just show placeholder with better styling
            except:
                pass
        
        if not album_art:
            # Placeholder icon
            icon_x = art_x + art_size // 2 - 25
            icon_y = art_y + art_size // 2 - 25
            draw.text((icon_x, icon_y), "♪", fill=self.spotify_green, font=self.font_huge)
        
        # Track info area
        info_x = art_x + art_size + 40
        info_y = art_y
        info_width = self.width - info_x - 60
        
        # "Now Playing" label
        draw.text((info_x, info_y), "NOW PLAYING", fill=self.gray, font=self.font_small)
        
        # Song title
        song_name = self.truncate_text(track_name, self.font_large, info_width)
        draw.text((info_x, info_y + 40), song_name, fill=self.white, font=self.font_large)
        
        # Artist(s)
        if artists:
            artist_names = ', '.join([artist.get('name', '') for artist in artists])
            artist_names = self.truncate_text(artist_names, self.font_medium, info_width)
            draw.text((info_x, info_y + 90), artist_names, fill=self.gray, font=self.font_medium)
        
        # Album name
        if album_name:
            album_name = self.truncate_text(album_name, self.font_small, info_width)
            draw.text((info_x, info_y + 135), album_name, fill=self.dark_gray, font=self.font_small)
        
        # Progress bar
        self.draw_progress_bar(draw, progress_ms, duration_ms, info_x, info_y + 180, info_width)
        
        # Control buttons
        self.draw_control_buttons(draw, playback_state, is_playing)
        
        # Device info
        if playback_state and playback_state.get('device'):
            device_name = playback_state.get('device', {}).get('name', 'Unknown Device')
        else:
            device_name = 'Unknown Device'
        draw.text((info_x, self.height - 80), f"Playing on: {device_name}", fill=self.dark_gray, font=self.font_tiny)
        
        
    
    def draw_progress_bar(self, draw, progress_ms, duration_ms, x, y, width):
        
        """Draw playback progress bar"""
        # Calculate progress
        if duration_ms > 0:
            progress = progress_ms / duration_ms
        else:
            progress = 0
        
        # Progress bar
        bar_height = 6
        bar_width = min(width - 100, 350)  # Leave space for time stamps
        
        # Background
        draw.rectangle((x, y, x + bar_width, y + bar_height), fill=self.light_bg)
        
        # Progress fill
        if progress > 0:
            fill_width = int(bar_width * progress)
            draw.rectangle((x, y, x + fill_width, y + bar_height), fill=self.spotify_green)
        
        # Time stamps
        current_time = self.format_duration(progress_ms)
        total_time = self.format_duration(duration_ms)
        
        draw.text((x, y + 15), current_time, fill=self.gray, font=self.font_tiny)
        draw.text((x + bar_width - 40, y + 15), total_time, fill=self.gray, font=self.font_tiny)
    
    def draw_control_buttons(self, draw, playback_state, is_playing):
        """Draw playback control buttons"""
        shuffle_state = playback_state.get('shuffle_state', False) if playback_state else False
        repeat_state = playback_state.get('repeat_state', 'off') if playback_state else 'off'
        
        # Control area
        controls_y = self.height - 140
        button_size = 50
        large_button_size = 70
        
        # Center the controls
        total_width = 5 * button_size + large_button_size
        start_x = (self.width - total_width) // 2
        
        # Shuffle button
        shuffle_color = self.spotify_green if shuffle_state else self.light_bg
        draw.rectangle((start_x, controls_y, start_x + button_size, controls_y + button_size), 
                      fill=shuffle_color, outline=self.gray, width=2)
        draw.text((start_x + 15, controls_y + 10), "🔀", fill=self.white, font=self.font_small)
        
        # Previous button
        prev_x = start_x + button_size + 20
        draw.rectangle((prev_x, controls_y, prev_x + button_size, controls_y + button_size), 
                      fill=self.light_bg, outline=self.gray, width=2)
        draw.text((prev_x + 10, controls_y + 8), "⏮", fill=self.white, font=self.font_medium)
        
        # Play/Pause button (larger)
        play_x = prev_x + button_size + 20
        play_y = controls_y - 10
        play_color = self.spotify_green if is_playing else self.accent_blue
        
        draw.ellipse((play_x, play_y, play_x + large_button_size, play_y + large_button_size), 
                    fill=play_color)
        
        symbol = "⏸" if is_playing else "▶"
        symbol_x = play_x + (30 if is_playing else 25)
        draw.text((symbol_x, play_y + 15), symbol, fill=self.white, font=self.font_large)
        
        # Next button
        next_x = play_x + large_button_size + 20
        draw.rectangle((next_x, controls_y, next_x + button_size, controls_y + button_size), 
                      fill=self.light_bg, outline=self.gray, width=2)
        draw.text((next_x + 10, controls_y + 8), "⏭", fill=self.white, font=self.font_medium)
        
        # Repeat button
        repeat_x = next_x + button_size + 20
        repeat_color = self.spotify_green if repeat_state != 'off' else self.light_bg
        draw.rectangle((repeat_x, controls_y, repeat_x + button_size, controls_y + button_size), 
                      fill=repeat_color, outline=self.gray, width=2)
        
        repeat_symbol = "🔂" if repeat_state == 'track' else "🔁"
        draw.text((repeat_x + 15, controls_y + 10), repeat_symbol, fill=self.white, font=self.font_small)
    
    def draw_idle_screen(self, draw):
        """Draw screen when no music is playing"""
        # Centered content
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Large Spotify icon
        icon_size = 100
        draw.ellipse((center_x - icon_size//2, center_y - icon_size//2 - 50, 
                     center_x + icon_size//2, center_y + icon_size//2 - 50), 
                    fill=self.card_bg, outline=self.spotify_green, width=4)
        
        draw.text((center_x - 35, center_y - 85), "♪", fill=self.spotify_green, font=self.font_huge)
        
        # Status messages
        draw.text((center_x - 120, center_y + 20), "No music playing", 
                 fill=self.gray, font=self.font_large)
        
        draw.text((center_x - 180, center_y + 65), "Open Spotify and start playing a song", 
                 fill=self.dark_gray, font=self.font_medium)
        
        # Instructions
        draw.text((center_x - 150, center_y + 120), "Listening for Spotify activity...", 
                 fill=self.dark_gray, font=self.font_small)
    
    def format_duration(self, ms):
        """Format milliseconds to MM:SS"""
        if not ms:
            return "0:00"
        
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

class SpotifyCarThingController:
    def __init__(self, lcd_port='COM3', lcd_baud=115200):
        """Initialize the Spotify Car Thing controller"""
        self.spotify_client = SpotifyClient()
        self.display = LCDDisplayController(lcd_port, lcd_baud)
        self.ui = SpotifyCarThingUI()
        
        self.running = False
        self.update_thread = None
        self.current_track = None
        self.playback_state = None
        
        # Update intervals
        self.fast_update_interval = 1.0  # 1 second when playing
        self.slow_update_interval = 5.0  # 5 seconds when idle
        
    def start(self):
        """Start the Spotify Car Thing"""
        print("🚗 Starting Spotify Car Thing...")
        
        # Connect to display
        if not self.display.connect():
            print("❌ Failed to connect to LCD display")
            return False
        print("✅ Connected to display on", self.display.port if hasattr(self.display, 'port') else "LCD")
        
        # Test Spotify connection
        if not self.test_spotify_connection():
            print("❌ Spotify connection failed")
            return False
        
        # Show startup screen
        self.show_startup_screen()
        
        # Start update loop
        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        
        print("✅ Spotify Car Thing is running!")
        print("🎵 Play music in Spotify to see it on the display")
        print("Press Ctrl+C to stop")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
        
        return True
    
    
    
    def test_spotify_connection(self):
        """Test if Spotify API is working"""
        try:
            # Try to get current user info
            user_info = self.spotify_client.get_current_user()
            if user_info:
                print(f"✅ Connected to Spotify as: {user_info.get('display_name', 'Unknown User')}")
                return True
            else:
                print("⚠️ Spotify API connected but no user info")
                return True  # Still allow to run
        except Exception as e:
            print(f"❌ Spotify connection test failed: {e}")
            return False
    
    def show_startup_screen(self):
        """Show startup screen"""
        img = Image.new('RGB', (1024, 600), color=(18, 18, 18))
        draw = ImageDraw.Draw(img)
        
        # Startup message
        draw.text((400, 250), "Starting Spotify Car Thing...", 
                 fill=(30, 215, 96), font=self.ui.font_large)
        draw.text((450, 320), "Connecting to Spotify...", 
                 fill=(180, 180, 180), font=self.ui.font_medium)
        
        self.display.send_image(img)
        time.sleep(2)
    
    def update_loop(self):
        """Main update loop"""
        last_update = 0
        consecutive_errors = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Determine update interval based on playback state
                is_playing = False
                if self.current_track:
                    is_playing = self.current_track.get('is_playing', False)
                elif self.playback_state:
                    is_playing = self.playback_state.get('is_playing', False)
                    
                update_interval = (self.fast_update_interval if is_playing 
                                 else self.slow_update_interval)
                
                # Update if enough time has passed
                if current_time - last_update >= update_interval:
                    # Get current track info
                    self.current_track = self.spotify_client.get_current_track()
                    
                    # Get playback state (sometimes different from current track)
                    self.playback_state = self.spotify_client.get_playback_state()
                    
                    # Create and display UI
                    display_img = self.ui.create_spotify_display(
                        self.current_track, self.playback_state)
                    
                    success = self.display.send_image(display_img)
                    
                    if success:
                        consecutive_errors = 0
                        last_update = current_time
                        
                        # Log current state
                        self.log_current_state()
                    else:
                        consecutive_errors += 1
                        print(f"⚠️ Display update failed ({consecutive_errors}/5)")
                        
                        if consecutive_errors >= 5:
                            print("❌ Too many display errors, stopping...")
                            break
                
                # Sleep for a short time
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Update loop error: {e}")
                consecutive_errors += 1
                time.sleep(2)  # Wait before retrying
                
                if consecutive_errors >= 10:
                    print("❌ Too many errors, stopping update loop")
                    break
    
    def log_current_state(self):
        """Log current playback state"""
        if self.current_track and self.current_track.get('track_name'):
            track_name = self.current_track.get('track_name', 'Unknown')
            artist_string = self.current_track.get('artist_string', 'Unknown Artist')
            
            is_playing = self.current_track.get('is_playing', False)
            progress_ms = self.current_track.get('progress_ms', 0)
            duration_ms = self.current_track.get('duration_ms', 0)
            
            # Format progress
            progress_str = self.ui.format_duration(progress_ms)
            duration_str = self.ui.format_duration(duration_ms)
            
            status = "▶️ " if is_playing else "⏸️ "
            print(f"{status}{track_name} - {artist_string} ({progress_str}/{duration_str})")
            
            # Show any errors
            if self.current_track.get('error'):
                print(f"⚠️ API Error: {self.current_track['error']}")
        else:
            print("🔇 No music playing")
            if self.current_track and self.current_track.get('error'):
                print(f"⚠️ Error: {self.current_track['error']}")
    
    def stop(self):
        """Stop the Spotify Car Thing"""
        print("\n🛑 Stopping Spotify Car Thing...")
        self.running = False
        
        # Wait for update thread to finish
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=3)
        
        # Show goodbye screen
        try:
            img = Image.new('RGB', (1024, 600), color=(18, 18, 18))
            draw = ImageDraw.Draw(img)
            draw.text((450, 280), "Goodbye!", fill=(30, 215, 96), font=self.ui.font_large)
            self.display.send_image(img)
        except:
            pass
        
        # Disconnect display
        try:
            self.display.disconnect()
        except:
            pass
        print("👋 Spotify Car Thing stopped!")

def main():
    """Main function to run the Spotify Car Thing"""
    print("🎵 Spotify Car Thing Clone")
    print("=" * 40)
    
    # Get LCD port settings
    port = input("Enter LCD COM port (default COM3): ").strip()
    if not port:
        port = "COM3"
    
    baud_input = input("Enter baud rate (default 115200): ").strip()
    try:
        baud = int(baud_input) if baud_input else 115200
    except ValueError:
        baud = 115200
        print("Invalid baud rate, using 115200")
    
    print(f"Using {port} at {baud} baud")
    
    # Create and start the Car Thing
    car_thing = SpotifyCarThingController(port, baud)
    
    try:
        car_thing.start()
    except KeyboardInterrupt:
        car_thing.stop()
    except Exception as e:
        print(f"❌ Error: {e}")
        car_thing.stop()

if __name__ == "__main__":
    main()