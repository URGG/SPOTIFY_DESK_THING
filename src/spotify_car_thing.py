#!/usr/bin/env python3
"""
Spotify Car Display - Your Custom Spotify Car Thing
This version includes enhanced loading screens with animations and better state management
"""

import time
import sys
import os
import math
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import threading

# Import your Spotify client
from spotify_client import SpotifyClient

# Add LCD library path
current_dir = os.path.dirname(os.path.abspath(__file__))
turing_root_path = os.path.join(current_dir, 'turing-smart-screen-python-main')
sys.path.insert(0, turing_root_path)

from library.lcd.lcd_comm_rev_a import LcdCommRevA
from library.lcd.lcd_comm_rev_b import LcdCommRevB
from library.lcd.lcd_comm import LcdComm


class LoadingScreenManager:
    """Manages various loading screen states for Spotify display"""
    
    # Animation constants
    DOT_ANIMATION_SPEED = 10  # frames per dot change
    SPINNER_ROTATION_SPEED = 0.2
    SPINNER_FADE_SPEED = 5    # frames per fade step
    
    # Color constants
    ERROR_COLOR = (255, 100, 100)
    
    def __init__(self, parent_display):
        self.display = parent_display
        self._cached_spinner_positions = {}
    
    def create_loading_screen(self, message="Connecting...", show_progress=False, progress=0):
        """Create Spotify-style loading screen with logo and optional progress"""
        image = Image.new('RGB', (self.display.logical_width, self.display.logical_height), 
                         self.display.bg_color)
        draw = ImageDraw.Draw(image)
        
        # Draw Spotify logo in center
        center_x = self.display.logical_width // 2
        center_y = self.display.logical_height // 2 - 30
        
        self.display.draw_spotify_logo(draw, center_x, center_y, size=80)
        
        # Dynamic message below logo
        font = self.display.get_font(24)
        
        bbox = draw.textbbox((0, 0), message, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.display.logical_width - text_width) // 2
        y = center_y + 60
        
        draw.text((x, y), message, fill=self.display.secondary_color, font=font)
        
        # Optional progress bar
        if show_progress:
            progress_y = y + 40
            progress_width = 200
            progress_height = 4
            progress_x = (self.display.logical_width - progress_width) // 2
            
            self.display.draw_progress_bar(draw, progress_x, progress_y, progress_width, progress_height, progress / 100)
            
            # Progress percentage
            percent_text = f"{int(progress)}%"
            percent_font = self.display.get_font(16)
            bbox = draw.textbbox((0, 0), percent_text, font=percent_font)
            text_width = bbox[2] - bbox[0]
            percent_x = (self.display.logical_width - text_width) // 2
            draw.text((percent_x, progress_y + 15), percent_text, fill=self.display.secondary_color, font=percent_font)
        
        return image
    
    def create_animated_loading_screen(self, frame=0, message_base="Connecting"):
        """Create animated loading screen with rotating dots"""
        image = Image.new('RGB', (self.display.logical_width, self.display.logical_height), 
                         self.display.bg_color)
        draw = ImageDraw.Draw(image)
        
        # Draw Spotify logo in center
        center_x = self.display.logical_width // 2
        center_y = self.display.logical_height // 2 - 30
        
        self.display.draw_spotify_logo(draw, center_x, center_y, size=80)
        
        # Animated message with dots
        dot_count = (frame // self.DOT_ANIMATION_SPEED) % 4  # Change dots every 10 frames, cycle 0-3
        dots = "." * dot_count
        message = message_base + dots
        
        font = self.display.get_font(24)
        bbox = draw.textbbox((0, 0), message, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.display.logical_width - text_width) // 2
        y = center_y + 60
        
        draw.text((x, y), message, fill=self.display.secondary_color, font=font)
        
        # Animated loading indicator (spinning circles)
        self.draw_loading_spinner(draw, center_x, y + 50, frame)
        
        return image
    
    def draw_loading_spinner(self, draw, center_x, center_y, frame):
        """Draw animated loading spinner"""
        radius = 15
        dot_radius = 3
        num_dots = 8
        
        for i in range(num_dots):
            angle = (i * 2 * math.pi / num_dots) + (frame * self.SPINNER_ROTATION_SPEED)
            dot_x = center_x + radius * math.cos(angle)
            dot_y = center_y + radius * math.sin(angle)
            
            # Fade dots based on position
            alpha = (i + frame // self.SPINNER_FADE_SPEED) % num_dots
            brightness = int(255 * (alpha / num_dots))
            dot_color = (brightness, brightness, brightness)
            
            draw.ellipse([
                dot_x - dot_radius, dot_y - dot_radius,
                dot_x + dot_radius, dot_y + dot_radius
            ], fill=dot_color)
    
    def create_auth_loading_screen(self):
        """Create loading screen specifically for authentication"""
        return self.create_loading_screen("Authenticating with Spotify...")
    
    def create_track_loading_screen(self):
        """Create loading screen for loading track data"""
        return self.create_loading_screen("Loading track information...")
    
    def create_reconnecting_screen(self, frame=0):
        """Create animated loading screen for reconnection attempts"""
        return self.create_animated_loading_screen(frame, "Reconnecting")
    
    def create_error_screen(self, error_message="Connection failed"):
        """Create error screen with retry indication"""
        image = Image.new('RGB', (self.display.logical_width, self.display.logical_height), 
                         self.display.bg_color)
        draw = ImageDraw.Draw(image)
        
        # Draw Spotify logo in center (dimmed)
        center_x = self.display.logical_width // 2
        center_y = self.display.logical_height // 2 - 50
        logo_size = 60
        
        # Try to use downloaded logo first (dimmed), fallback to drawn logo
        logo_img = self._get_logo_image(logo_size, dimmed=True)
        if logo_img:
            logo_x = center_x - logo_size // 2
            logo_y = center_y - logo_size // 2
            if logo_img.mode == 'RGBA':
                image.paste(logo_img, (logo_x, logo_y), logo_img)
            else:
                image.paste(logo_img, (logo_x, logo_y))
        else:
            # Fallback to drawn dimmed logo
            dimmed_accent = tuple(c // 2 for c in self.display.accent_color)
            self._draw_dimmed_logo(draw, center_x, center_y, dimmed_accent, size=logo_size)
        
        # Error message
        font = self.display.get_font(20)
        bbox = draw.textbbox((0, 0), error_message, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.display.logical_width - text_width) // 2
        y = center_y + 40
        
        draw.text((x, y), error_message, fill=self.ERROR_COLOR, font=font)
        
        # Retry message
        retry_font = self.display.get_font(16)
        retry_text = "Retrying in a moment..."
        bbox = draw.textbbox((0, 0), retry_text, font=retry_font)
        text_width = bbox[2] - bbox[0]
        x = (self.display.logical_width - text_width) // 2
        y = center_y + 70
        
        draw.text((x, y), retry_text, fill=self.display.secondary_color, font=retry_font)
        
        return image
    
    def _draw_dimmed_logo(self, draw, center_x, center_y, dimmed_color, size=60):
        """Draw a dimmed version of the Spotify logo for error states"""
        # Draw the dimmed green circle background first
        circle_radius = size // 2
        circle_bbox = [
            center_x - circle_radius, center_y - circle_radius,
            center_x + circle_radius, center_y + circle_radius
        ]
        draw.ellipse(circle_bbox, fill=dimmed_color)
        
        # Now draw the 3 black curved lines on top (same as normal logo)
        line_color = (0, 0, 0)  # Pure black
        
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


class SpotifyCarDisplay:
    def __init__(self):
        """Initialize the Spotify Car Display"""
        print("🎵 Initializing Spotify Car Display...")
        
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
        
        # Initialize loading screen manager
        self.loading_manager = LoadingScreenManager(self)
        
        print("✅ Spotify Car Display initialized!")
        
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
        """Draw the Spotify logo (curved lines)"""
        # Spotify logo consists of curved lines
        line_color = self.accent_color
        line_width = size // 15
        
        # Draw three curved lines
        for i, curve_height in enumerate([0.7, 0.5, 0.3]):
            y_offset = (i - 1) * (size // 8)
            curve_y = center_y + y_offset
            
            # Create curved line points
            points = []
            for x in range(-size//2, size//2, 2):
                # Create a curve using sine wave
                curve = math.sin(x / (size/6)) * (size * curve_height * 0.1)
                points.append((center_x + x, curve_y + curve))
            
            # Draw the curve as connected line segments
            for j in range(len(points) - 1):
                x1, y1 = points[j]
                x2, y2 = points[j + 1]
                
                # Draw thick line by drawing multiple thin lines
                for offset in range(-line_width//2, line_width//2 + 1):
                    draw.line([(x1, y1 + offset), (x2, y2 + offset)], fill=line_color, width=1)
    
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
    
    def enhanced_update_loop(self):
        """Enhanced update loop with better loading states"""
        print("🔄 Starting enhanced display update loop...")
        
        # Show initial loading
        loading_image = self.loading_manager.create_loading_screen("Starting up...")
        self.display_image(loading_image)
        time.sleep(1)
        
        # Show auth check
        auth_image = self.loading_manager.create_auth_loading_screen()
        self.display_image(auth_image)
        time.sleep(1)
        
        # Initial check for current track
        print("🎵 Checking for active playback...")
        initial_track = self.get_current_track()
        
        # Show appropriate initial screen
        if initial_track:
            print(f"🎵 Found active track: {initial_track['title']}")
            # Show track loading screen briefly
            track_loading = self.loading_manager.create_track_loading_screen()
            self.display_image(track_loading)
            time.sleep(0.5)
            
            # Then show the actual track
            display_image = self.create_spotify_display(initial_track)
            self.display_image(display_image)
            self.last_track_id = initial_track['id']
            self.last_progress_ms = initial_track.get('progress_ms', 0)
        else:
            print("⏸️  No music currently playing - showing idle screen")
            # Show "no music playing" screen immediately
            idle_image = self.create_spotify_display(None)
            self.display_image(idle_image)
            self.last_track_id = None
            self.last_progress_ms = 0
        
        frame_counter = 0
        error_count = 0
        max_errors = 3
        
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
                        
                        # No loading screen - just update directly for seamless experience
                    
                    elif abs(progress_ms - self.last_progress_ms) > 2000:
                        should_update = True
                        print(f"⏯️  Progress update: {self.format_time(progress_ms)}")
                    
                    self.last_track_id = track_id
                    self.last_progress_ms = progress_ms
                    error_count = 0  # Reset error count on success
                    
                else:
                    if self.last_track_id is not None:
                        should_update = True
                        print("⏹️  Music stopped")
                        self.last_track_id = None
                        self.last_progress_ms = 0
                
                if should_update:
                    display_image = self.create_spotify_display(current_track)
                    self.display_image(display_image)
                
                frame_counter += 1
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping display...")
                break
            except Exception as e:
                print(f"❌ Update error: {e}")
                error_count += 1
                
                if error_count >= max_errors:
                    error_image = self.loading_manager.create_error_screen("Multiple connection failures")
                    self.display_image(error_image)
                    time.sleep(3)
                    error_count = 0
                else:
                    # Show animated reconnecting screen
                    reconnect_image = self.loading_manager.create_reconnecting_screen(frame_counter)
                    self.display_image(reconnect_image)
                
                time.sleep(2)
    
    def start(self):
        """Start the Spotify Car Display"""
        try:
            print("🚗 Starting Enhanced Spotify Car Display...")
            print("Press Ctrl+C to stop")
            
            if not self.spotify.is_authenticated():
                print("❌ Not authenticated with Spotify. Please run authentication first.")
                return
            
            self.enhanced_update_loop()
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        finally:
            self.stop()
    
    def stop(self):
        """Clean shutdown"""
        self.running = False
        try:
            goodbye_image = Image.new('RGB', (self.logical_width, self.logical_height), self.bg_color)
            draw = ImageDraw.Draw(goodbye_image)
            font = self.get_font(24)
            text = "Goodbye!"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.logical_width - text_width) // 2
            y = (self.logical_height - (bbox[3] - bbox[1])) // 2
            draw.text((x, y), text, fill=self.accent_color, font=font)
            self.display_image(goodbye_image)
            time.sleep(2)
            
            self.lcd.Clear()
            self.lcd.ScreenOff()
            print("📱 Display turned off")
        except:
            pass


if __name__ == "__main__":
    print("🎵 Enhanced Spotify Car Display v3.0 - Loading Screen System")
    print("=" * 60)
    
    try:
        display = SpotifyCarDisplay()
        display.start()
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        print("Make sure:")
        print("1. LCD is connected via USB")
        print("2. Spotify app is open and playing")
        print("3. spotify_client.py is in the same folder")
        print("4. You've authenticated with Spotify")