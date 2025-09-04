import os
import time
import threading
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import struct
import serial

# Import your LCDHelper and SpotifyClient
from lcd_send_helper import LCDHelper
from spotify_client import SpotifyClient

class SpotifyCarThingUI:
    def __init__(self, width=320, height=480, enable_album_art=False, simple_mode=True):
        self.width = width
        self.height = height
        self.enable_album_art = enable_album_art
        self.simple_mode = simple_mode
        self.spotify_green = (30, 215, 96)
        self.dark_bg = (18, 18, 18)
        self.light_bg = (40, 40, 40)
        self.card_bg = (35, 35, 35)
        self.white = (255, 255, 255)
        self.gray = (180, 180, 180)
        self.dark_gray = (120, 120, 120)
        self.accent_blue = (45, 125, 255)
        self.load_fonts()

    def load_fonts(self):
        if self.simple_mode:
            print("🔧 Using simple fonts")
            default = ImageFont.load_default()
            self.font_huge = default
            self.font_large = default
            self.font_medium = default
            self.font_small = default
            self.font_tiny = default
            return
        try:
            self.font_huge = ImageFont.truetype("arial.ttf", 58)
            self.font_large = ImageFont.truetype("arial.ttf", 42)
            self.font_medium = ImageFont.truetype("arial.ttf", 32)
            self.font_small = ImageFont.truetype("arial.ttf", 22)
            self.font_tiny = ImageFont.truetype("arial.ttf", 16)
        except Exception as e:
            print(f"⚠️ Using default fonts: {e}")
            default = ImageFont.load_default()
            self.font_huge = default
            self.font_large = default
            self.font_medium = default
            self.font_small = default
            self.font_tiny = default

    def safe_truncate_text(self, text, max_length):
        if not text: return "Unknown"
        safe_text = ''.join(char for char in str(text) if ord(char) < 128)
        return safe_text[:max_length - 3] + "..." if len(safe_text) > max_length else safe_text

    def safe_format_duration(self, ms):
        try: return f"{int(ms//60000)}:{int((ms%60000)//1000):02d}" if ms and ms >= 0 else "0:00"
        except: return "0:00"

    def create_spotify_display_simple(self, current_track=None, playback_state=None):
        img = Image.new('RGB', (self.width, self.height), color=self.dark_bg)
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, self.width, 70), fill=self.light_bg)
        draw.text((10, 10), "SPOTIFY", fill=self.spotify_green, font=self.font_medium)
        current_time = datetime.now().strftime("%H:%M")
        draw.text((self.width - 80, 10), current_time, fill=self.white, font=self.font_medium)
        if current_track and self.is_track_data_simple(current_track):
            self.draw_simple_track_info(draw, current_track, playback_state)
        else:
            self.draw_simple_idle_screen(draw)
        return img

    def is_track_data_simple(self, current_track):
        try: return len(str(current_track.get('item', {}).get('name', ''))) <= 30 and len(str(current_track.get('item', {}).get('artists', []))) <= 50
        except: return False

    def draw_simple_track_info(self, draw, current_track, playback_state):
        track_name = current_track.get('item', {}).get('name', 'Unknown Track')
        artists = current_track.get('item', {}).get('artists', [])
        progress_ms = current_track.get('progress_ms', 0)
        duration_ms = current_track.get('item', {}).get('duration_ms', 0)
        is_playing = current_track.get('is_playing', False)
        start_y = 80
        info_x = 10
        safe_track_name = self.safe_truncate_text(track_name, 25)
        draw.text((info_x, start_y), safe_track_name, fill=self.white, font=self.font_large)
        if artists: draw.text((info_x, start_y + 40), self.safe_truncate_text(artists[0].get('name', 'Unknown'), 20), fill=self.gray, font=self.font_medium)
        self.draw_simple_progress_bar(draw, progress_ms, duration_ms, info_x, start_y + 80)
        draw.text((info_x, start_y + 120), "⏸ PAUSED" if not is_playing else "▶ PLAYING", fill=self.spotify_green, font=self.font_medium)

    def draw_simple_progress_bar(self, draw, progress_ms, duration_ms, x, y):
        progress = min(progress_ms / duration_ms, 1.0) if duration_ms > 0 and progress_ms >= 0 else 0.0
        bar_width, bar_height = 300, 8
        draw.rectangle((x, y, x + bar_width, y + bar_height), fill=self.light_bg)
        if progress > 0: draw.rectangle((x, y, x + int(bar_width * progress), y + bar_height), fill=self.spotify_green)
        draw.text((x, y + 15), f"{self.safe_format_duration(progress_ms)} / {self.safe_format_duration(duration_ms)}", fill=self.gray, font=self.font_small)

    def draw_simple_idle_screen(self, draw):
        center_x, center_y = self.width // 2, self.height // 2
        draw.text((center_x - 25, center_y), "Idle", fill=self.gray, font=self.font_medium)

    def create_spotify_display(self, current_track=None, playback_state=None):
        return self.create_spotify_display_simple(current_track, playback_state)

class EnhancedDisplayController:
    def __init__(self, base_helper):
        self.base_helper = base_helper

    def send_image_uncompressed(self, image, use_bgr=False, baudrate=9600):  # Use your proven stable rate
        try:
            if image.mode != 'RGB': image = image.convert('RGB')
            image = image.resize((self.base_helper.width, self.base_helper.height), Image.Resampling.LANCZOS)
            
            # Use the delays that work!
            time.sleep(0.1)
            
            success = self.base_helper.send_image(image, use_bgr=use_bgr, baudrate=baudrate)
            print(f"[Enhanced] Image sent successfully")
            
            # Post-send delay
            time.sleep(0.2)
            
            return success
        except Exception as e:
            print(f"[Enhanced] Error: {e}")
            return False

    def send_image_with_retry(self, image, max_retries=2, use_bgr=False, baudrate=9600):
        for attempt in range(max_retries):
            try:
                print(f"📡 Attempt {attempt + 1}/{max_retries} at {baudrate} baud")
                if self.send_image_uncompressed(image, use_bgr=use_bgr, baudrate=baudrate):
                    print("✅ Success")
                    return True
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(1)
        print("❌ All retries failed")
        return False

class SpotifyCarThingController:
    def __init__(self, lcd_port='COM3', lcd_baud=9600, simple_mode=True, use_enhanced=False):
        self.spotify_client = SpotifyClient()
        self.display = LCDHelper(lcd_port, lcd_baud)
        self.enhanced = EnhancedDisplayController(self.display) if use_enhanced else None
        self.ui = SpotifyCarThingUI(enable_album_art=False, simple_mode=simple_mode)
        self.running = False
        self.update_thread = None
        self.current_track = None
        self.playback_state = None
        self.fast_update_interval = 8.0  # Even slower - stability first
        self.slow_update_interval = 15.0
        self.stable_baudrate = lcd_baud
        print(f"🔧 Running in {'SIMPLE' if simple_mode else 'FULL'} mode")
        print(f"🧪 Enhanced sender: {'ON' if self.enhanced else 'OFF'}")
        print(f"📡 Using proven stable baud rate: {lcd_baud}")

    def start(self):
        print("🚀 Starting Spotify Car Thing...")
        if not self.display.ser.is_open:  
            print("❌ Failed to connect to LCD display")
            return False
        print("✅ Connected to display")
        
        if not self.test_spotify_connection():
            print("❌ Spotify connection failed")
            return False
        
        self.show_startup_screen()
        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        print("✅ Spotify Car Thing is running!")
        print("🎵 Play music in Spotify to see it on the display")
        print("Press Ctrl+C to stop")
        print("🧪 Set TEST_MODE=2 for progressive UI tests")
        
        try:
            while self.running: time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
        return True

    def test_spotify_connection(self):
        try:
            user_info = self.spotify_client.get_current_user()
            if user_info:
                print(f"✅ Connected to Spotify as: {user_info.get('display_name', 'Unknown User')}")
                return True
            return True
        except Exception as e:
            print(f"❌ Spotify connection test failed: {e}")
            return False

    def show_startup_screen(self):
        img = Image.new('RGB', (320, 480), color=(18, 18, 18))
        draw = ImageDraw.Draw(img)
        draw.text((10, 200), "Starting...", fill=(30, 215, 96))
        self._send_image(img)
        time.sleep(3)

    def _send_image(self, pil_image):
        """Send image with your proven stable settings"""
        if self.enhanced:
            return self.enhanced.send_image_with_retry(
                pil_image, 
                use_bgr=True, 
                baudrate=self.stable_baudrate
            )
        return self.display.send_image(pil_image, use_bgr=True, baudrate=self.stable_baudrate)

    def progressive_ui_test(self):
        """Progressive test - build complexity step by step"""
        print("🧪 PROGRESSIVE UI TEST - Building complexity step by step")
        
        # Step 1: Your proven solid colors (we know these work!)
        print("📊 Step 1: Testing solid colors (proven to work)")
        test_img = Image.new('RGB', (240, 320), color=(255, 0, 0))
        print("   Red screen")
        self._send_image(test_img)
        time.sleep(3)
        
        test_img = Image.new('RGB', (240, 320), color=(0, 255, 0))
        print("   Green screen")
        self._send_image(test_img)
        time.sleep(3)
        
        test_img = Image.new('RGB', (240, 320), color=(0, 0, 255))
        print("   Blue screen")
        self._send_image(test_img)
        time.sleep(3)
        
        # Step 2: Simple shapes
        print("📊 Step 2: Testing simple shapes")
        test_img = Image.new('RGB', (240, 320), color=(18, 18, 18))
        draw = ImageDraw.Draw(test_img)
        draw.rectangle((50, 50, 190, 150), fill=(255, 0, 0))
        print("   Rectangle on dark background")
        self._send_image(test_img)
        time.sleep(3)
        
        # Step 3: Multiple rectangles
        print("📊 Step 3: Testing multiple rectangles")
        test_img = Image.new('RGB', (240, 320), color=(18, 18, 18))
        draw = ImageDraw.Draw(test_img)
        draw.rectangle((10, 10, 230, 50), fill=(40, 40, 40))  # Header bar
        draw.rectangle((10, 70, 230, 120), fill=(35, 35, 35))  # Content area
        print("   UI-like rectangles")
        self._send_image(test_img)
        time.sleep(3)
        
        # Step 4: Add simple text
        print("📊 Step 4: Testing simple text")
        test_img = Image.new('RGB', (240, 320), color=(18, 18, 18))
        draw = ImageDraw.Draw(test_img)
        draw.rectangle((10, 10, 230, 50), fill=(40, 40, 40))
        draw.text((20, 20), "SPOTIFY", fill=(30, 215, 96))
        print("   Header with text")
        self._send_image(test_img)
        time.sleep(3)
        
        # Step 5: More complex layout
        print("📊 Step 5: Testing basic Spotify layout")
        test_img = Image.new('RGB', (240, 320), color=(18, 18, 18))
        draw = ImageDraw.Draw(test_img)
        # Header
        draw.rectangle((0, 0, 240, 50), fill=(40, 40, 40))
        draw.text((10, 15), "SPOTIFY", fill=(30, 215, 96))
        # Content area
        draw.text((10, 70), "Test Track", fill=(255, 255, 255))
        draw.text((10, 100), "Test Artist", fill=(180, 180, 180))
        print("   Basic Spotify UI layout")
        self._send_image(test_img)
        time.sleep(5)
        
        print("✅ Progressive test complete!")
        print("   If any step failed, we know exactly where the problem starts")
        
        self.stop()

    def update_loop(self):
        last_update = 0
        test_mode = os.getenv("TEST_MODE", "0")
        
        if test_mode == "1":
            print("🧪 TEST MODE 1: Solid color test (proven to work)")
            # Your proven solid color test
            test_img = Image.new('RGB', (240, 320), color=(255, 0, 0))
            print("📊 Testing with red screen")
            self._send_image(test_img)
            time.sleep(5)
            
            test_img = Image.new('RGB', (240, 320), color=(0, 255, 0))
            print("📊 Testing with green screen")  
            self._send_image(test_img)
            time.sleep(5)
            
            test_img = Image.new('RGB', (240, 320), color=(0, 0, 255))
            print("📊 Testing with blue screen")
            self._send_image(test_img)
            time.sleep(5)
            
            print("🧪 Solid color test complete")
            self.stop()
            return
            
        elif test_mode == "2":
            self.progressive_ui_test()
            return
        
        while self.running:
            try:
                current_time = time.time()
                is_playing = self.current_track.get('is_playing', False) if self.current_track else False
                update_interval = self.fast_update_interval if is_playing else self.slow_update_interval
                
                if current_time - last_update >= update_interval:
                    print(f"🔄 Updating display...")
                    self.current_track = self.spotify_client.get_current_track()
                    self.playback_state = self.spotify_client.get_playback_state()
                    display_img = self.ui.create_spotify_display(self.current_track, self.playback_state)
                    
                    success = self._send_image(display_img)
                    if success: 
                        last_update = current_time
                        print(f"✅ Display updated successfully")
                    else:
                        print(f"❌ Display update failed")
                    
                    time.sleep(3)  # Longer delay between real updates
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Update loop error: {e}")
                time.sleep(8)  # Much longer wait on error
        self.stop()

    def stop(self):
        if not self.running:
            self.display.close()
            return
        print("🛑 Stopping Spotify Car Thing...")
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=3)
        self.display.close()
        print("✅ Stopped.")

if __name__ == "__main__":
    port = os.getenv("LCD_PORT", "COM3")
    baud = int(os.getenv("LCD_BAUD", "9600"))  # Your proven stable rate!
    simple = os.getenv("SIMPLE_MODE", "1") != "0"
    enhanced = os.getenv("ENHANCED_SENDER", "1") == "1"

    print(f"🔧 Configuration (PROVEN STABLE):")
    print(f"   Port: {port}")
    print(f"   Baud Rate: {baud}")
    print(f"   Simple Mode: {simple}")
    print(f"   Enhanced: {enhanced}")
    print(f"")
    print(f"🧪 Test modes available:")
    print(f"   TEST_MODE=1 - Your proven solid color test")
    print(f"   TEST_MODE=2 - Progressive UI complexity test")
    print(f"   Normal run - Full Spotify display")

    controller = SpotifyCarThingController(
        lcd_port=port,
        lcd_baud=baud,  # Keep your stable 9600
        simple_mode=simple,
        use_enhanced=enhanced
    )
    controller.start()