import os
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import time

try:
    import sys
    import os
    
    # Add the turing repo root to path (where main.py is)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    turing_root_path = os.path.join(current_dir, 'turing-smart-screen-python-main')
    
    if os.path.exists(turing_root_path):
        sys.path.insert(0, turing_root_path)
    
    # Import the display module like main.py does
    from library.display import display
    
    # Create a wrapper class that matches our interface
    class TuringSmartScreen:
        def __init__(self, display_type="3.5inch", orientation=0):
            print(f"Initializing Turing Smart Screen: {display_type}")
            
            # Initialize the display like main.py does
            display.initialize_display()
            
            self.display_type = display_type
            self.orientation = orientation
            
            # Set dimensions based on display type
            if display_type == "3.5inch":
                self.width, self.height = 320, 480
            elif display_type == "5inch":
                self.width, self.height = 800, 480
            elif display_type == "8.8inch":
                self.width, self.height = 1920, 480
            else:
                self.width, self.height = 320, 480
                
        def get_dimensions(self):
            return (self.width, self.height)
            
        def display_image(self, image):
            """Send PIL image to the display"""
            try:
                # The display module has an 'lcd' attribute
                if hasattr(display, 'lcd'):
                    lcd = display.lcd
                    
                    # Ensure image is the right size
                    width, height = image.size
                    if width != self.width or height != self.height:
                        image = image.resize((self.width, self.height), Image.Resampling.LANCZOS)
                    
                    # Try different methods to send the image to LCD
                    if hasattr(lcd, 'DisplayPILImage'):
                        lcd.DisplayPILImage(image, 0, 0)
                        print("✅ Image sent to LCD display via DisplayPILImage!")
                    elif hasattr(lcd, 'DisplayBitmap'):
                        # Convert PIL to bitmap format
                        image_rgb = image.convert('RGB')
                        bitmap_data = image_rgb.tobytes()
                        lcd.DisplayBitmap(bitmap_data, 0, 0, self.width, self.height)
                        print("✅ Image sent to LCD display via DisplayBitmap!")
                    elif hasattr(lcd, 'display_pil_image'):
                        lcd.display_pil_image(image)
                        print("✅ Image sent to LCD display!")
                    else:
                        # Show what methods are available on the LCD object
                        available_methods = [method for method in dir(lcd) if not method.startswith('_') and 'display' in method.lower()]
                        print(f"Available LCD methods with 'display': {available_methods}")
                        
                        all_methods = [method for method in dir(lcd) if not method.startswith('_')]
                        print(f"All LCD methods: {all_methods}")
                        
                        # Try a generic method name
                        if hasattr(lcd, 'send_image'):
                            lcd.send_image(image)
                            print("✅ Image sent via send_image!")
                        else:
                            raise AttributeError("No suitable display method found on LCD object")
                else:
                    raise AttributeError("No lcd attribute found in display module")
                    
            except Exception as e:
                print(f"Error sending image to LCD: {e}")
                # Save for debugging
                filename = f"debug_display_{int(time.time())}.png"
                image.save(filename)
                print(f"Saved debug image to {filename}")
                print("Image creation is working - just need to find the right LCD method")
        
        def close(self):
            """Clean shutdown"""
            try:
                if hasattr(display, 'turn_off'):
                    display.turn_off()
            except:
                pass
    
    SCREEN_AVAILABLE = True
    print("✅ Successfully imported Turing Smart Screen display library!")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Falling back to mock mode...")
    SCREEN_AVAILABLE = False
    
    # Mock class for testing without hardware
    class TuringSmartScreen:
        def __init__(self, display_type="3.5inch", orientation=0):
            self.display_type = display_type
            # Set dimensions based on display type
            if display_type == "3.5inch":
                self.dimensions = (320, 480)
            elif display_type == "5inch":
                self.dimensions = (800, 480)
            elif display_type == "8.8inch":
                self.dimensions = (1920, 480)
            else:
                self.dimensions = (320, 480)
            
        def get_dimensions(self):
            return self.dimensions
            
        def display_image(self, image):
            # Save the image so you can see what it looks like
            filename = f"mock_display_{int(time.time())}.png"
            # Use absolute path to make sure we know where it's saved
            current_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(current_dir, filename)
            
            try:
                image.save(filepath)
                print(f"Mock: Saved display image to {filepath}")
                return filepath
            except Exception as e:
                print(f"Error saving mock image: {e}")
                # Try saving to current working directory as fallback
                try:
                    fallback_path = filename
                    image.save(fallback_path)
                    print(f"Mock: Saved display image to {os.path.abspath(fallback_path)}")
                    return fallback_path
                except Exception as e2:
                    print(f"Failed to save image anywhere: {e2}")
                    return None


class SpotifyDisplayController:
    def __init__(self, display_type="3.5inch", orientation=0):
        """
        Initialize the Spotify display controller
        
        Args:
            display_type: Screen type ("3.5inch", "5inch", "8.8inch")
            orientation: Screen orientation (0, 90, 180, 270)
        """
        print(f"Initializing display: {display_type}, orientation: {orientation}")
        try:
            self.screen = TuringSmartScreen(display_type=display_type, orientation=orientation)
            self.screen_width, self.screen_height = self.screen.get_dimensions()
            print(f"Display initialized successfully! Dimensions: {self.screen_width}x{self.screen_height}")
        except Exception as e:
            print(f"Error initializing display: {e}")
            print("Make sure your LCD is connected via USB")
            raise
        
        # Color scheme
        self.bg_color = (18, 18, 18)  # Dark background like Spotify
        self.text_color = (255, 255, 255)  # White text
        self.accent_color = (30, 215, 96)  # Spotify green
        self.progress_bg = (83, 83, 83)  # Gray progress background
        
        # Font sizes (adjust based on your screen size)
        self.title_font_size = 16
        self.artist_font_size = 14
        self.time_font_size = 12
        
        # Layout constants
        self.album_art_size = min(120, self.screen_height // 3)
        self.margin = 10
        
        # Cache for album art
        self.current_album_url = None
        self.cached_album_art = None
        
    def get_font(self, size):
        """Get font with fallback to default"""
        try:
            # Try to load a nice font (adjust path as needed)
            return ImageFont.truetype("/System/Library/Fonts/Arial.ttf", size)
        except:
            try:
                return ImageFont.truetype("arial.ttf", size)
            except:
                return ImageFont.load_default()
    
    def download_album_art(self, image_url, size=None):
        """Download and resize album art"""
        if not image_url:
            return self.create_placeholder_art(size or self.album_art_size)
            
        if image_url == self.current_album_url and self.cached_album_art:
            return self.cached_album_art
            
        try:
            response = requests.get(image_url, timeout=5)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            if size:
                image = image.resize((size, size), Image.Resampling.LANCZOS)
            
            # Cache the result
            self.current_album_url = image_url
            self.cached_album_art = image
            
            return image
            
        except Exception as e:
            print(f"Error downloading album art: {e}")
            return self.create_placeholder_art(size or self.album_art_size)
    
    def create_placeholder_art(self, size):
        """Create a placeholder album art"""
        placeholder = Image.new('RGB', (size, size), self.bg_color)
        draw = ImageDraw.Draw(placeholder)
        
        # Draw a simple music note icon
        center = size // 2
        draw.ellipse([center-20, center-10, center+20, center+10], fill=self.accent_color)
        draw.rectangle([center+15, center-20, center+20, center], fill=self.accent_color)
        
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
        """Truncate text to fit within max_width"""
        if not text:
            return ""
            
        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        
        if draw.textlength(text, font=font) <= max_width:
            return text
        
        # Add ellipsis
        while len(text) > 3 and draw.textlength(text + "...", font=font) > max_width:
            text = text[:-1]
        
        return text + "..." if text else ""
    
    def draw_progress_bar(self, draw, x, y, width, height, progress):
        """Draw a progress bar"""
        # Background
        draw.rectangle([x, y, x + width, y + height], fill=self.progress_bg)
        
        # Progress
        if progress > 0:
            progress_width = int(width * min(progress, 1.0))
            draw.rectangle([x, y, x + progress_width, y + height], fill=self.accent_color)
    
    def update_display(self, track_info):
        """
        Update the display with current track information
        
        Args:
            track_info: Dictionary containing:
                - title: Song title
                - artist: Artist name
                - album: Album name
                - album_art_url: URL to album art image
                - progress_ms: Current playback position in ms
                - duration_ms: Total track duration in ms
                - is_playing: Boolean if currently playing
        """
        # Create a new image
        image = Image.new('RGB', (self.screen_width, self.screen_height), self.bg_color)
        draw = ImageDraw.Draw(image)
        
        # Get fonts
        title_font = self.get_font(self.title_font_size)
        artist_font = self.get_font(self.artist_font_size)
        time_font = self.get_font(self.time_font_size)
        
        current_y = self.margin
        
        # Album art (top section)
        if track_info.get('album_art_url'):
            album_art = self.download_album_art(track_info['album_art_url'], self.album_art_size)
            art_x = (self.screen_width - self.album_art_size) // 2
            image.paste(album_art, (art_x, current_y))
        
        current_y += self.album_art_size + self.margin
        
        # Track title
        title = track_info.get('title', 'Unknown Track')
        max_text_width = self.screen_width - (2 * self.margin)
        title_truncated = self.truncate_text(title, title_font, max_text_width)
        
        title_bbox = draw.textbbox((0, 0), title_truncated, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.screen_width - title_width) // 2
        
        draw.text((title_x, current_y), title_truncated, fill=self.text_color, font=title_font)
        current_y += title_bbox[3] - title_bbox[1] + 5
        
        # Artist name
        artist = track_info.get('artist', 'Unknown Artist')
        artist_truncated = self.truncate_text(artist, artist_font, max_text_width)
        
        artist_bbox = draw.textbbox((0, 0), artist_truncated, font=artist_font)
        artist_width = artist_bbox[2] - artist_bbox[0]
        artist_x = (self.screen_width - artist_width) // 2
        
        draw.text((artist_x, current_y), artist_truncated, fill=(180, 180, 180), font=artist_font)
        current_y += artist_bbox[3] - artist_bbox[1] + 15
        
        # Progress bar and time
        progress_ms = track_info.get('progress_ms', 0)
        duration_ms = track_info.get('duration_ms', 1)
        progress = progress_ms / duration_ms if duration_ms > 0 else 0
        
        # Time labels
        current_time = self.format_time(progress_ms)
        total_time = self.format_time(duration_ms)
        
        time_y = current_y
        draw.text((self.margin, time_y), current_time, fill=self.text_color, font=time_font)
        
        total_time_bbox = draw.textbbox((0, 0), total_time, font=time_font)
        total_time_width = total_time_bbox[2] - total_time_bbox[0]
        draw.text((self.screen_width - self.margin - total_time_width, time_y), total_time, fill=self.text_color, font=time_font)
        
        # Progress bar
        time_bbox = draw.textbbox((0, 0), "0:00", font=time_font)
        time_height = time_bbox[3] - time_bbox[1]
        progress_y = current_y + time_height + 5
        progress_bar_width = self.screen_width - (2 * self.margin)
        
        self.draw_progress_bar(draw, self.margin, progress_y, progress_bar_width, 4, progress)
        
        # Play/pause indicator
        if track_info.get('is_playing', False):
            # Draw play symbol (triangle)
            symbol_y = progress_y + 15
            symbol_size = 8
            center_x = self.screen_width // 2
            
            points = [
                (center_x - symbol_size//2, symbol_y),
                (center_x + symbol_size//2, symbol_y + symbol_size//2),
                (center_x - symbol_size//2, symbol_y + symbol_size)
            ]
            draw.polygon(points, fill=self.accent_color)
        else:
            # Draw pause symbol (two rectangles)
            symbol_y = progress_y + 15
            symbol_size = 8
            center_x = self.screen_width // 2
            
            draw.rectangle([center_x - 6, symbol_y, center_x - 2, symbol_y + symbol_size], fill=self.accent_color)
            draw.rectangle([center_x + 2, symbol_y, center_x + 6, symbol_y + symbol_size], fill=self.accent_color)
        
        # Send image to display
        try:
            self.screen.display_image(image)
        except Exception as e:
            print(f"Error updating display: {e}")
    
    def show_loading(self):
        """Show a loading screen"""
        image = Image.new('RGB', (self.screen_width, self.screen_height), self.bg_color)
        draw = ImageDraw.Draw(image)
        
        font = self.get_font(18)
        text = "Loading Spotify..."
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (self.screen_width - text_width) // 2
        y = (self.screen_height - text_height) // 2
        
        draw.text((x, y), text, fill=self.accent_color, font=font)
        
        try:
            self.screen.display_image(image)
        except Exception as e:
            print(f"Error showing loading screen: {e}")
    
    def show_no_playback(self):
        """Show when no music is playing"""
        image = Image.new('RGB', (self.screen_width, self.screen_height), self.bg_color)
        draw = ImageDraw.Draw(image)
        
        font = self.get_font(16)
        text = "No music playing"
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (self.screen_width - text_width) // 2
        y = (self.screen_height - text_height) // 2
        
        draw.text((x, y), text, fill=(128, 128, 128), font=font)
        
        # Draw a large music note
        center_x = self.screen_width // 2
        note_y = y - 60
        draw.ellipse([center_x-25, note_y, center_x+25, note_y+20], outline=self.accent_color, width=3)
        draw.rectangle([center_x+20, note_y-30, center_x+25, note_y+10], fill=self.accent_color)
        
        try:
            self.screen.display_image(image)
        except Exception as e:
            print(f"Error showing no playback screen: {e}")
    
    def close(self):
        """Clean up resources"""
        if hasattr(self.screen, 'close'):
            self.screen.close()


# Example usage
if __name__ == "__main__":
    # Test the display controller
    controller = SpotifyDisplayController(display_type="3.5inch")
    
    # Show loading
    controller.show_loading()
    time.sleep(2)
    
    # Test with sample track data
    sample_track = {
        'title': 'Bohemian Rhapsody',
        'artist': 'Queen',
        'album': 'A Night at the Opera',
        'album_art_url': 'https://i.scdn.co/image/ab67616d0000b273ce4f1737bc8a646c8c4bd25a',
        'progress_ms': 125000,  # 2:05
        'duration_ms': 355000,  # 5:55
        'is_playing': True
    }
    
    controller.update_display(sample_track)
    
    print("Display updated! Press Ctrl+C to exit...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        controller.close()
        print("\nDisplay controller closed.")