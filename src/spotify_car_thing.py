#!/usr/bin/env python3

import time
import sys
import os
import math
import psutil
import threading
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Import your Spotify client
from spotify_client import SpotifyClient

# Add LCD library path
current_dir = os.path.dirname(os.path.abspath(__file__))
turing_root_path = os.path.join(current_dir, 'turing-smart-screen-python-main')
sys.path.insert(0, turing_root_path)

from library.lcd.lcd_comm_rev_a import LcdCommRevA
from library.lcd.lcd_comm_rev_b import LcdCommRevB
from library.lcd.lcd_comm import LcdComm


class PowerMonitor:
    """Monitor computer power state and manage display accordingly"""
    
    def __init__(self, display_instance):
        self.display = display_instance
        self.monitoring = False
        self.monitor_thread = None
        self.last_battery_plugged = None
        self.is_laptop = self._detect_laptop()
        
    def _detect_laptop(self):
        """Detect if running on a laptop (has battery)"""
        try:
            battery = psutil.sensors_battery()
            return battery is not None
        except:
            return False
    
    def start_monitoring(self):
        """Start monitoring power state"""
        if not self.is_laptop:
            print("🔌 Desktop detected - skipping power monitoring")
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🔋 Power monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring power state"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_loop(self):
        """Monitor loop for power state changes"""
        while self.monitoring:
            try:
                battery = psutil.sensors_battery()
                if battery:
                    current_plugged = battery.power_plugged
                    
                    if self.last_battery_plugged is not None:
                        if current_plugged and not self.last_battery_plugged:
                            print("🔌 Power connected - waking display")
                            self._wake_display()
                        elif not current_plugged and self.last_battery_plugged:
                            print("🔋 On battery power - display staying active")
                    
                    self.last_battery_plugged = current_plugged
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"⚠️ Power monitoring error: {e}")
                time.sleep(10)
    
    def _wake_display(self):
        """Wake up the display"""
        try:
            self.display.lcd.ScreenOn()
            # Force a display update
            if hasattr(self.display, '_force_update'):
                self.display._force_update()
        except Exception as e:
            print(f"❌ Error waking display: {e}")


class SpotifyDeskThing:
    def __init__(self):
        """Initialize the Spotify Desk Thing"""
        print("🎵 Initializing Spotify Desk Thing v4.0...")
        
        # Initialize Spotify client
        self.spotify = SpotifyClient()
        
        # Initialize LCD 
        self.init_lcd()
        
        # Create landscape layout but display it rotated
        self.logical_width = 480   # What we design for (landscape)
        self.logical_height = 320  # What we design for (landscape)
        self.physical_width = 320  # What the screen actually is (portrait)
        self.physical_height = 480 # What the screen actually is (portrait)
        
        # Spotify-inspired color scheme
        self.bg_color = (18, 18, 18)        
        self.text_color = (255, 255, 255)   
        self.accent_color = (30, 215, 96)   
        self.secondary_color = (179, 179, 179)  
        self.progress_bg = (83, 83, 83)     
        self.card_bg = (40, 40, 40)         
        
        # Layout for landscape design
        self.album_art_size = 180
        self.margin = 20
        
        # Font sizes for landscape
        self.title_font_size = 24
        self.artist_font_size = 18
        self.album_font_size = 16
        self.time_font_size = 14
        
        # Cache for album art
        self.current_album_url = None
        self.cached_album_art = None
        
        # Update control
        self.running = True
        self.last_track_id = None
        self.last_progress_ms = 0
        
        # Initialize power monitor
        self.power_monitor = PowerMonitor(self)
        
        print("✅ Spotify Desk Thing v4.0 initialized!")
        
    def init_lcd(self):
        """Initialize LCD communication"""
        try:
            self.lcd = LcdCommRevA()
            print("✅ LCD Rev A connected!")
        except Exception as e:
            print(f"Rev A failed: {e}, trying Rev B...")
            try:
                self.lcd = LcdCommRevB()
                print("✅ LCD Rev B connected!")
            except Exception as e:
                print(f"Rev B failed: {e}, using base LCD...")
                self.lcd = LcdComm()
                print("✅ Base LCD connected!")
        
        # Keep orientation as portrait (0) - we'll rotate the image instead
        try:
            self.lcd.SetOrientation(0)  # Portrait mode
            print("📱 Display set to portrait mode (will rotate image)")
        except Exception as e:
            print(f"⚠️  Could not set orientation: {e}")
    
    def get_font(self, size):
        """Get font with fallback"""
        try:
            return ImageFont.truetype("arial.ttf", size)
        except:
            try:
                return ImageFont.truetype("/Windows/Fonts/arial.ttf", size)
            except:
                try:
                    return ImageFont.truetype("/System/Library/Fonts/Arial.ttf", size)
                except:
                    try:
                        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
                    except:
                        return ImageFont.load_default()
    
    def create_startup_screen(self):
        """Create simple startup screen - no animation"""
        image = Image.new('RGB', (self.logical_width, self.logical_height), self.bg_color)
        draw = ImageDraw.Draw(image)
        
        # Draw Spotify logo in center
        center_x = self.logical_width // 2
        center_y = self.logical_height // 2 - 20
        
        self.draw_spotify_logo(draw, center_x, center_y, size=100)
        
        # Welcome text
        welcome_font = self.get_font(28)
        welcome_text = "Spotify Desk Thing"
        bbox = draw.textbbox((0, 0), welcome_text, font=welcome_font)
        text_width = bbox[2] - bbox[0]
        x = (self.logical_width - text_width) // 2
        y = center_y + 70
        
        draw.text((x, y), welcome_text, fill=self.text_color, font=welcome_font)
        
        return image
    
    def create_goodbye_screen(self):
        """Create simple goodbye screen - no animation"""
        image = Image.new('RGB', (self.logical_width, self.logical_height), self.bg_color)
        draw = ImageDraw.Draw(image)
        
        # Draw Spotify logo in center
        center_x = self.logical_width // 2
        center_y = self.logical_height // 2 - 20
        
        self.draw_spotify_logo(draw, center_x, center_y, size=80)
        
        # Goodbye text
        goodbye_font = self.get_font(24)
        goodbye_text = "Thanks for listening!"
        bbox = draw.textbbox((0, 0), goodbye_text, font=goodbye_font)
        text_width = bbox[2] - bbox[0]
        x = (self.logical_width - text_width) // 2
        y = center_y + 60
        
        draw.text((x, y), goodbye_text, fill=self.text_color, font=goodbye_font)
        
        return image
    
    def download_album_art(self, image_url):
        """Download and cache album artwork"""
        if not image_url:
            return self.create_placeholder_art()
            
        if image_url == self.current_album_url and self.cached_album_art:
            return self.cached_album_art
            
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            image = image.resize((self.album_art_size, self.album_art_size), Image.Resampling.LANCZOS)
            
            # Cache the result
            self.current_album_url = image_url
            self.cached_album_art = image
            
            return image
            
        except Exception as e:
            print(f"❌ Error downloading album art: {e}")
            return self.create_placeholder_art()
    
    def create_placeholder_art(self):
        """Create Spotify-style placeholder album art"""
        placeholder = Image.new('RGB', (self.album_art_size, self.album_art_size), (60, 60, 60))
        draw = ImageDraw.Draw(placeholder)
        
        # Draw Spotify-style music icon
        center_x = self.album_art_size // 2
        center_y = self.album_art_size // 2
        
        note_color = (140, 140, 140)
        draw.ellipse([center_x - 15, center_y + 5, center_x - 5, center_y + 15], fill=note_color)
        draw.rectangle([center_x - 5, center_y - 25, center_x - 3, center_y + 10], fill=note_color)
        
        flag_points = [
            (center_x - 3, center_y - 25),
            (center_x + 12, center_y - 20),
            (center_x + 12, center_y - 10),
            (center_x - 3, center_y - 15)
        ]
        draw.polygon(flag_points, fill=note_color)
        
        return placeholder
    
    def format_time(self, ms):
        """Convert milliseconds to MM:SS format"""
        if not ms:
            return "0:00"
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def truncate_text(self, text, font, max_width):
        """Truncate text to fit width"""
        if not text:
            return ""
            
        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        
        if draw.textlength(text, font=font) <= max_width:
            return text
        
        while len(text) > 3 and draw.textlength(text + "...", font=font) > max_width:
            text = text[:-1]
        
        return text + "..." if text else ""
    
    def draw_progress_bar(self, draw, x, y, width, height, progress):
        """Draw Spotify-style progress bar"""
        # Background
        draw.rectangle([x, y, x + width, y + height], fill=self.progress_bg)
        
        # Progress fill
        if progress > 0:
            progress_width = int(width * min(progress, 1.0))
            if progress_width > 0:
                draw.rectangle([x, y, x + progress_width, y + height], fill=self.accent_color)
                
                # Add thumb
                if progress_width > 6:
                    thumb_x = x + progress_width - 3
                    thumb_y = y + height // 2
                    draw.ellipse([thumb_x - 3, thumb_y - 3, thumb_x + 3, thumb_y + 3], fill=self.text_color)
    
    def create_spotify_display(self, track_data):
        """Create the main Spotify display in landscape layout"""
        # Create landscape image (will be rotated later)
        image = Image.new('RGB', (self.logical_width, self.logical_height), self.bg_color)
        draw = ImageDraw.Draw(image)
        
        # Get fonts
        title_font = self.get_font(self.title_font_size)
        artist_font = self.get_font(self.artist_font_size)
        album_font = self.get_font(self.album_font_size)
        time_font = self.get_font(self.time_font_size)
        
        if track_data:
            # Layout for landscape: Album art on left, info on right
            art_x = self.margin
            art_y = (self.logical_height - self.album_art_size) // 2
            
            # Album art
            album_art = self.download_album_art(track_data.get('album_art_url'))
            image.paste(album_art, (art_x, art_y))
            
            # Info area starts after album art
            info_x = art_x + self.album_art_size + self.margin * 2
            info_width = self.logical_width - info_x - self.margin
            
            # Start positioning text
            current_y = self.margin + 10
            
            # Track title
            title = track_data.get('title', 'Unknown Track')
            title_truncated = self.truncate_text(title, title_font, info_width)
            draw.text((info_x, current_y), title_truncated, fill=self.text_color, font=title_font)
            current_y += 35
            
            # Artist name
            artist = track_data.get('artist', 'Unknown Artist')
            artist_truncated = self.truncate_text(artist, artist_font, info_width)
            draw.text((info_x, current_y), artist_truncated, fill=self.secondary_color, font=artist_font)
            current_y += 30
            
            # Album name
            album = track_data.get('album', '')
            if album:
                album_truncated = self.truncate_text(album, album_font, info_width)
                draw.text((info_x, current_y), album_truncated, fill=self.secondary_color, font=album_font)
                current_y += 25
            
            current_y += 30
            
            # Progress section
            progress_ms = track_data.get('progress_ms', 0)
            duration_ms = track_data.get('duration_ms', 1)
            progress = progress_ms / duration_ms if duration_ms > 0 else 0
            
            # Progress bar
            progress_y = current_y
            progress_width = info_width - 20
            progress_height = 6
            self.draw_progress_bar(draw, info_x + 10, progress_y, progress_width, progress_height, progress)
            current_y += 25
            
            # Time display
            current_time = self.format_time(progress_ms)
            total_time = self.format_time(duration_ms)
            
            draw.text((info_x + 10, current_y), current_time, fill=self.secondary_color, font=time_font)
            
            time_bbox = draw.textbbox((0, 0), total_time, font=time_font)
            time_width = time_bbox[2] - time_bbox[0]
            draw.text((info_x + progress_width - time_width + 10, current_y), total_time, fill=self.secondary_color, font=time_font)
            
            # Play/pause indicator
            is_playing = track_data.get('is_playing', False)
            symbol_y = current_y + 35
            symbol_x = info_x + info_width - 40
            
            button_size = 30
            draw.ellipse([symbol_x, symbol_y, symbol_x + button_size, symbol_y + button_size], 
                        fill=self.text_color if is_playing else self.secondary_color)
            
            center_x = symbol_x + button_size // 2
            center_y = symbol_y + button_size // 2
            
            if is_playing:
                bar_width = 3
                bar_height = 10
                draw.rectangle([center_x - 5, center_y - bar_height//2, 
                              center_x - 5 + bar_width, center_y + bar_height//2], fill=self.bg_color)
                draw.rectangle([center_x + 2, center_y - bar_height//2, 
                              center_x + 2 + bar_width, center_y + bar_height//2], fill=self.bg_color)
            else:
                triangle_size = 6
                points = [
                    (center_x - triangle_size//2, center_y - triangle_size),
                    (center_x + triangle_size, center_y),
                    (center_x - triangle_size//2, center_y + triangle_size)
                ]
                draw.polygon(points, fill=self.bg_color)
            
            # Spotify logo
            logo_font = self.get_font(12)
            draw.text((self.logical_width - 60, self.logical_height - 20), "Spotify", fill=self.accent_color, font=logo_font)
        
        else:
            # No music playing
            no_music_font = self.get_font(28)
            subtitle_font = self.get_font(18)
            
            main_text = "No music playing"
            bbox = draw.textbbox((0, 0), main_text, font=no_music_font)
            text_width = bbox[2] - bbox[0]
            x = (self.logical_width - text_width) // 2
            y = self.logical_height // 2 - 30
            draw.text((x, y), main_text, fill=self.secondary_color, font=no_music_font)
            
            subtitle = "Open Spotify and start playing music"
            bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            text_width = bbox[2] - bbox[0]
            x = (self.logical_width - text_width) // 2
            y = self.logical_height // 2 + 10
            draw.text((x, y), subtitle, fill=(120, 120, 120), font=subtitle_font)
            
            logo_font = self.get_font(16)
            draw.text((self.logical_width - 80, self.logical_height - 25), "Spotify", fill=self.accent_color, font=logo_font)
        
        return image
    
    def draw_spotify_logo(self, draw, center_x, center_y, size=60):
        """Draw the proper Spotify logo - green circle with three curved horizontal lines"""
        # Draw the green circle background first
        circle_radius = size // 2
        circle_bbox = [
            center_x - circle_radius, center_y - circle_radius,
            center_x + circle_radius, center_y + circle_radius
        ]
        draw.ellipse(circle_bbox, fill=self.accent_color)
        
        # Now draw the 3 black curved lines on top
        line_color = (0, 0, 0)  # Pure black for contrast
        
        # Calculate line properties based on the official logo proportions
        line_spacing = size // 6  # Space between lines
        base_width = max(3, size // 18)  # Line thickness
        
        # Three lines with proper curves - positioned like the official logo
        lines_data = [
            {"y_offset": -line_spacing, "length_ratio": 0.75, "curve_intensity": 0.15},  # Top line - longest, most curved
            {"y_offset": 0, "length_ratio": 0.60, "curve_intensity": 0.12},             # Middle line
            {"y_offset": line_spacing, "length_ratio": 0.45, "curve_intensity": 0.10}   # Bottom line - shortest, least curved
        ]
        
        for i, line_data in enumerate(lines_data):
            y_pos = center_y + line_data["y_offset"]
            line_length = size * line_data["length_ratio"]
            curve_intensity = line_data["curve_intensity"]
            line_width = base_width + (2 - i)  # Lines get slightly thinner as they go down
            
            # Create smooth curved line using multiple small segments
            points = []
            num_segments = 20  # More segments = smoother curve
            
            for j in range(num_segments + 1):
                # Calculate x position along the line
                t = j / num_segments  # Parameter from 0 to 1
                x = center_x - line_length/2 + t * line_length
                
                # Create natural curve - parabolic arc
                curve_offset = -curve_intensity * size * (4 * t * (1 - t))  # Parabola: peaks at t=0.5
                y = y_pos + curve_offset
                
                points.append((x, y))
            
            # Draw the curved line as connected segments
            for j in range(len(points) - 1):
                x1, y1 = points[j]
                x2, y2 = points[j + 1]
                draw.line([(x1, y1), (x2, y2)], fill=line_color, width=line_width)
    
    def display_image(self, image):
        """Send image to LCD - rotate to fit portrait screen"""
        try:
            # Rotate the landscape image 90 degrees counter-clockwise to fit portrait screen
            rotated_image = image.rotate(90, expand=True)
            
            # Resize to fit the physical screen if needed
            if rotated_image.size != (self.physical_width, self.physical_height):
                rotated_image = rotated_image.resize((self.physical_width, self.physical_height), Image.Resampling.LANCZOS)
            
            self.lcd.DisplayPILImage(rotated_image, 0, 0)
            
        except Exception as e:
            print(f"❌ Display error: {e}")
    
    def get_current_track(self):
        """Get current Spotify track info"""
        try:
            playback = self.spotify.get_current_playback()
            
            if not playback or not playback.get('item'):
                return None
                
            track = playback['item']
            
            return {
                'id': track['id'],
                'title': track['name'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'album_art_url': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'progress_ms': playback.get('progress_ms', 0),
                'duration_ms': track['duration_ms'],
                'is_playing': playback.get('is_playing', False)
            }
            
        except Exception as e:
            print(f"❌ Error getting track info: {e}")
            return None
    
    def _force_update(self):
        """Force a display update - called by power monitor"""
        current_track = self.get_current_track()
        display_image = self.create_spotify_display(current_track)
        self.display_image(display_image)
    
    def update_loop(self):
        """Main update loop - FAST startup, no loading screens"""
        print("🔄 Starting main display loop...")
        
        # Get current track immediately - no loading screens
        current_track = self.get_current_track()
        
        if current_track:
            print(f"🎵 Found active track: {current_track['title']}")
            display_image = self.create_spotify_display(current_track)
            self.display_image(display_image)
            self.last_track_id = current_track['id']
            self.last_progress_ms = current_track.get('progress_ms', 0)
        else:
            print("⏸️  No music currently playing")
            idle_image = self.create_spotify_display(None)
            self.display_image(idle_image)
            self.last_track_id = None
            self.last_progress_ms = 0
        
        frame_counter = 0
        error_count = 0
        
        # Start power monitoring
        self.power_monitor.start_monitoring()
        
        while self.running:
            try:
                current_track = self.get_current_track()
                should_update = False
                
                if current_track:
                    track_id = current_track['id']
                    progress_ms = current_track.get('progress_ms', 0)
                    
                    if track_id != self.last_track_id:
                        should_update = True
                        if self.last_track_id is None:
                            print(f"▶️  Music started: {current_track['title']}")
                        else:
                            print(f"🎵 Track changed: {current_track['title']}")
                    elif abs(progress_ms - self.last_progress_ms) > 2000:
                        should_update = True
                    
                    self.last_track_id = track_id
                    self.last_progress_ms = progress_ms
                    error_count = 0
                    
                else:
                    if self.last_track_id is not None:
                        should_update = True
                        print("⏹️  Music stopped")
                        self.last_track_id = None
                        self.last_progress_ms = 0
                
                if should_update:
                    display_image = self.create_spotify_display(current_track)
                    self.display_image(display_image)
                
                time.sleep(0.5)  # Fast updates
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                error_count += 1
                if error_count > 3:
                    print("Multiple errors, taking a longer break...")
                    time.sleep(5)
                    error_count = 0
                else:
                    time.sleep(2)
        
        self.power_monitor.stop_monitoring()
    
    def start(self):
        """Start the Spotify Desk Thing - SUPER FAST"""
        try:
            print("🚀 Starting Spotify Desk Thing v4.0...")
            
            if not self.spotify.is_authenticated():
                print("❌ Not authenticated with Spotify. Please run authentication first.")
                return
            
            # Show startup screen for exactly 1 second
            print("🌟 Quick startup...")
            startup_image = self.create_startup_screen()
            self.display_image(startup_image)
            time.sleep(1.0)  # Exactly 1 second
            
            # Jump straight to main content
            self.update_loop()
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        finally:
            self.stop()
    
    def stop(self):
        """FAST shutdown"""
        self.running = False
        try:
            # Show goodbye for exactly 1 second
            print("👋 Quick goodbye...")
            goodbye_image = self.create_goodbye_screen()
            self.display_image(goodbye_image)
            time.sleep(1.0)  # Exactly 1 second
            
            # Turn off immediately
            self.lcd.Clear()
            self.lcd.ScreenOff()
            print("📱 Display off")
            
        except Exception as e:
            print(f"⚠️ Shutdown error: {e}")


if __name__ == "__main__":
    print("🎵 Spotify Desk Thing v4.0 - Fast & Clean")
    print("=" * 50)
    print("✨ Super fast startup and shutdown!")
    print("✨ 1 second startup, 1 second goodbye")
    print("✨ No loading screens or delays")
    print("=" * 50)
    
    try:
        display = SpotifyDeskThing()
        display.start()
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        print("Make sure:")
        print("1. LCD is connected via USB")
        print("2. Spotify app is open")
        print("3. spotify_client.py is in the same folder")
        print("4. You've authenticated with Spotify")
        print("5. psutil library is installed: pip install psutil")