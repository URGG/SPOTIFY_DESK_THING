import serial
import time
from PIL import Image, ImageDraw, ImageFont
import io
import threading

class LCDDisplayController:
    def __init__(self, port='COM3', baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.connected = False
        
    def connect(self):
        """Connect to the LCD display"""
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            self.connected = True
            print(f"✅ Connected to display on {self.port}")
            return True
        except Exception as e:
            print(f"❌ Error connecting to display: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from display"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.connected = False
            print("Disconnected from display")
    
    def send_image(self, img, method=1):
        """Send image to display with different methods"""
        if not self.connected or not self.ser:
            print("❌ Display not connected")
            return False
        
        try:
            if method == 1:
                # Method 1: Raw RGB565 (common for LCD displays)
                print("📤 Trying RGB565 format")
                img_rgb = img.convert('RGB')
                pixels = list(img_rgb.getdata())
                
                rgb565_data = bytearray()
                for r, g, b in pixels:
                    # Convert to RGB565
                    r565 = (r >> 3) << 11
                    g565 = (g >> 2) << 5
                    b565 = b >> 3
                    rgb565 = r565 | g565 | b565
                    rgb565_data.extend(rgb565.to_bytes(2, byteorder='little'))
                
                # Send dimension header + data
                header = bytearray()
                header.extend(b'\xAA\xBB')  # Start marker
                header.extend((1024).to_bytes(2, byteorder='little'))
                header.extend((600).to_bytes(2, byteorder='little'))
                
                self.ser.write(header)
                self.ser.write(rgb565_data)
                
            elif method == 2:
                # Method 2: Raw RGB888 with proper header
                print("📤 Trying RGB888 with header")
                img_rgb = img.convert('RGB')
                img_bytes = img_rgb.tobytes()
                
                header = bytearray()
                header.extend(b'\xFF\xD8')  # JPEG start marker
                header.extend((1024).to_bytes(4, byteorder='little'))
                header.extend((600).to_bytes(4, byteorder='little'))
                header.extend((3).to_bytes(1))  # 3 bytes per pixel
                
                self.ser.write(header)
                self.ser.write(img_bytes)
                
            elif method == 3:
                # Method 3: BMP format
                print("📤 Trying BMP format")
                buffer = io.BytesIO()
                img_rgb = img.convert('RGB')
                img_rgb.save(buffer, format='BMP')
                bmp_data = buffer.getvalue()
                
                self.ser.write(b'BM')
                self.ser.write(bmp_data[2:])
                
            elif method == 4:
                # Method 4: Line-by-line RGB
                print("📤 Trying line-by-line RGB")
                img_rgb = img.convert('RGB')
                
                # Send header
                self.ser.write(b'\x12\x34')
                self.ser.write((1024).to_bytes(2, byteorder='little'))
                self.ser.write((600).to_bytes(2, byteorder='little'))
                
                # Send line by line
                for y in range(600):
                    line_data = bytearray()
                    for x in range(1024):
                        pixel = img_rgb.getpixel((x, y))
                        line_data.extend(pixel)
                    
                    self.ser.write(b'\xAA')
                    self.ser.write(y.to_bytes(2, byteorder='little'))
                    self.ser.write(line_data)
                    time.sleep(0.001)
                    
            elif method == 5:
                # Method 5: JPEG with commands
                print("📤 Trying JPEG with display command")
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=95)
                img_bytes = buffer.getvalue()
                
                commands = [b'\x55\xAA\x01\x02', b'\xFF\xFE\xFD\xFC', b'\x00\x01\x02\x03']
                
                for cmd in commands:
                    self.ser.write(cmd)
                    self.ser.write(len(img_bytes).to_bytes(4, byteorder='little'))
                    self.ser.write(img_bytes)
                    time.sleep(0.1)
                    
            print(f"📤 Sent data using method {method}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending image: {e}")
            return False
    
    def create_spotify_dashboard(self, track_info=None):
        """Create a Spotify-styled dashboard image"""
        img = Image.new('RGB', (1024, 600), color=(18, 18, 18))
        draw = ImageDraw.Draw(img)
        
        try:
            font_title = ImageFont.truetype("arial.ttf", 36)
            font_large = ImageFont.truetype("arial.ttf", 48)
            font_medium = ImageFont.truetype("arial.ttf", 28)
            font_small = ImageFont.truetype("arial.ttf", 20)
        except:
            font_title = font_large = font_medium = font_small = ImageFont.load_default()
        
        spotify_green = (30, 215, 96)
        white = (255, 255, 255)
        gray = (180, 180, 180)
        
        draw.text((40, 30), "♪ SPOTIFY", fill=spotify_green, font=font_title)
        
        if track_info:
            draw.text((40, 120), "Now Playing", fill=gray, font=font_medium)
            song_name = track_info.get('name', 'Unknown Track')[:40]
            draw.text((40, 180), song_name, fill=white, font=font_large)
            artist_name = track_info.get('artist', 'Unknown Artist')[:50]
            draw.text((40, 240), artist_name, fill=gray, font=font_medium)
        else:
            draw.text((40, 200), "No track playing", fill=gray, font=font_large)
            draw.text((40, 260), "Start Spotify and play a song", fill=gray, font=font_medium)
        
        return img

def test_simple_colors():
    """Test with simple solid colors"""
    display = LCDDisplayController()
    if display.connect():
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green  
            (0, 0, 255),    # Blue
            (255, 255, 255), # White
            (0, 0, 0),      # Black
        ]
        
        for i, color in enumerate(colors):
            img = Image.new('RGB', (1024, 600), color=color)
            color_name = ['Red', 'Green', 'Blue', 'White', 'Black'][i]
            print(f"🎨 Sending {color_name} screen...")
            
            display.send_image(img, method=1)
            
            input(f"Do you see {color_name} on the LCD? Press Enter for next color...")
            
        display.disconnect()

def test_all_methods():
    """Test all different methods"""
    display = LCDDisplayController()
    if display.connect():
        # Create simple test image
        img = Image.new('RGB', (1024, 600), color=(255, 0, 0))  # Red background
        draw = ImageDraw.Draw(img)
        draw.rectangle((100, 100, 924, 500), fill=(0, 255, 0))  # Green rectangle
        draw.rectangle((200, 200, 824, 400), fill=(0, 0, 255))  # Blue rectangle
        
        for method in range(1, 6):
            print(f"\n🔄 Testing Method {method}...")
            display.send_image(img, method=method)
            
            response = input(f"Check LCD: Do you see colored rectangles? (y/n/better/worse): ")
            if response.lower() == 'y':
                print(f"✅ Method {method} works!")
                break
                
        display.disconnect()

def test_color_refinement():
    """Test colors with better RGB565 conversion"""
    display = LCDDisplayController()
    if display.connect():
        colors = [
            (255, 0, 0),    # Pure Red
            (0, 255, 0),    # Pure Green  
            (0, 0, 255),    # Pure Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 255, 255), # White
            (128, 128, 128), # Gray
            (0, 0, 0),      # Black
        ]
        
        for i, color in enumerate(colors):
            img = Image.new('RGB', (1024, 600), color=color)
            color_names = ['Red', 'Green', 'Blue', 'Yellow', 'Magenta', 'Cyan', 'White', 'Gray', 'Black']
            print(f"🎨 Sending {color_names[i]} screen...")
            
            display.send_image(img, method=1)
            
            response = input(f"What do you see? Expected: {color_names[i]} (describe what you actually see): ")
            print(f"Result: {response}")
            
        display.disconnect()

def test_simple_dashboard():
    """Test simple geometric dashboard"""
    display = LCDDisplayController()
    if display.connect():
        print("🎵 Testing SIMPLE geometric dashboard...")
        
        mock_track = {
            'name': 'Bohemian Rhapsody',
            'artist': 'Queen', 
            'progress_ms': 120000,
            'duration_ms': 300000,
            'is_playing': True
        }
        
        # Try geometric version first
        simple_img = display.create_simple_spotify_dashboard(mock_track)
        display.send_image(simple_img, method=1)
        
        print("You should see colored rectangles:")
        print("- Green bar at top (header)")
        print("- White rectangle (song info)")
        print("- Blue rectangle (more info)")  
        print("- Red rectangle (artist)")
        print("- Progress bar at bottom")
        print("- Green square (playing indicator)")
        
        response = input("Do you see colored rectangles instead of lines? (y/n): ")
        
        if response.lower() == 'y':
            print("✅ Simple dashboard works! Now trying pixel-perfect version...")
            
            # Try pixel-perfect version with text
            pixel_img = display.create_pixel_perfect_spotify(mock_track)
            display.send_image(pixel_img, method=1)
            
            print("Now you should see:")
            print("- Green SPOTIFY header")
            print("- White song name section")
            print("- Gray artist section") 
            print("- Progress bar")
            print("- Status indicator")
            
            input("Do you see text and sections clearly? Press Enter...")
        
        display.disconnect()

def test_progression():
    """Test progression from simple to complex"""
    display = LCDDisplayController()
    if display.connect():
        
        # Test 1: Pure geometric
        print("📊 Test 1: Pure geometric shapes")
        img1 = Image.new('RGB', (1024, 600), color=(0, 0, 0))
        draw = ImageDraw.Draw(img1)
        draw.rectangle((100, 100, 500, 200), fill=(255, 0, 0))
        draw.rectangle((100, 300, 500, 400), fill=(0, 255, 0))
        display.send_image(img1, method=1)
        input("See red and green rectangles? Press Enter...")
        
        # Test 2: Add simple text
        print("📊 Test 2: Add simple text")
        img2 = Image.new('RGB', (1024, 600), color=(0, 0, 0))
        draw = ImageDraw.Draw(img2)
        draw.rectangle((100, 100, 900, 200), fill=(255, 255, 255))
        font = ImageFont.load_default()
        draw.text((120, 130), "SPOTIFY DASHBOARD TEST", fill=(0, 0, 0), font=font)
        display.send_image(img2, method=1)
        input("See white rectangle with black text? Press Enter...")
        
        # Test 3: Full simple dashboard
        print("📊 Test 3: Simple dashboard")
        mock_data = {'name': 'Test Song', 'artist': 'Test Artist', 'is_playing': True, 'progress_ms': 60000, 'duration_ms': 180000}
        img3 = display.create_pixel_perfect_spotify(mock_data)
        display.send_image(img3, method=1)
        input("See full dashboard? Press Enter...")
        
        display.disconnect()

def create_test_pattern():
    """Create a test pattern to verify colors work correctly"""
    display = LCDDisplayController()
    if display.connect():
        # Create a test pattern image
        img = Image.new('RGB', (1024, 600), color=(0, 0, 0))  # Black background
        draw = ImageDraw.Draw(img)
        
        # Color bars
        colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255), (255,255,255)]
        bar_width = 1024 // len(colors)
        
        for i, color in enumerate(colors):
            x1 = i * bar_width
            x2 = (i + 1) * bar_width
            draw.rectangle((x1, 0, x2, 600), fill=color)
        
        # Add text
        try:
            font = ImageFont.truetype("arial.ttf", 48)
        except:
            font = ImageFont.load_default()
            
        draw.text((50, 300), "COLOR TEST", fill=(0, 0, 0), font=font)
        
        print("🌈 Sending color test pattern...")
        display.send_image(img, method=1)
        
        print("You should see vertical color bars: Red, Green, Blue, Yellow, Magenta, Cyan, White")
        input("What do you see? Press Enter...")
        display.disconnect()