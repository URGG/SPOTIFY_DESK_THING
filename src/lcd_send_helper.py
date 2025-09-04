import serial
import time
from PIL import Image
import struct

class LCDHelper:
    def __init__(self, port="COM3", baudrate=9600, width=240, height=320):
        self.width = width
        self.height = height
        self.ser = serial.Serial(port, baudrate, timeout=2)
        time.sleep(2)
        print(f"[LCD] Connected to {port} at {baudrate} baud")
        print(f"[LCD] Resolution: {width}x{height}, Format: RGB565")

    def rgb_to_rgb565(self, r, g, b):
        """Convert 24-bit RGB to 16-bit RGB565"""
        # RGB565: 5 bits red, 6 bits green, 5 bits blue
        return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

    def image_to_rgb565(self, image):
        """Convert PIL image to RGB565 byte array"""
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Ensure correct resolution
        image = image.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
        # Convert to RGB565
        rgb565_data = bytearray()
        pixels = image.load()
        
        for y in range(self.height):
            for x in range(self.width):
                r, g, b = pixels[x, y]
                rgb565 = self.rgb_to_rgb565(r, g, b)
                
                # Little endian 16-bit (most common for LCDs)
                rgb565_data.append(rgb565 & 0xFF)        # Low byte
                rgb565_data.append((rgb565 >> 8) & 0xFF) # High byte
        
        return rgb565_data

    def send_image_basic(self, image):
        """Send image using basic protocol (no display area setup)"""
        try:
            print(f"[LCD] Converting image to RGB565...")
            rgb565_data = self.image_to_rgb565(image)
            
            print(f"[LCD] Sending {len(rgb565_data)} bytes...")
            
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            # Use your working protocol
            self.ser.write(b"\xA5\x5A")
            time.sleep(0.05)
            self.ser.write(len(rgb565_data).to_bytes(4, 'big'))
            time.sleep(0.05)
            self.ser.write(rgb565_data)
            time.sleep(0.05)
            self.ser.write(b"\x5A\xA5")
            self.ser.flush()
            
            print(f"[LCD] Image sent successfully")
            time.sleep(0.2)
            return True
            
        except Exception as e:
            print(f"[LCD] Error: {e}")
            return False

    def send_image_with_area(self, image):
        """Send image with display area setup commands - FIXED VERSION"""
        try:
            print(f"[LCD] Converting image to RGB565...")
            rgb565_data = self.image_to_rgb565(image)
            
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            print(f"[LCD] Setting display area to full screen...")
            
            # FIXED: Proper 16-bit coordinate handling
            x_start = 0
            x_end = self.width - 1    # 239
            y_start = 0  
            y_end = self.height - 1   # 319 (this was causing the overflow!)
            
            # Column Address Set (X coordinates: 0 to width-1)
            self.ser.write(b"\x2A")  # CASET command
            time.sleep(0.01)
            # Send as 16-bit values (big endian)
            self.ser.write(struct.pack('>HH', x_start, x_end))  # 0, 239
            time.sleep(0.01)
            
            # Page Address Set (Y coordinates: 0 to height-1)  
            self.ser.write(b"\x2B")  # PASET command
            time.sleep(0.01)
            # Send as 16-bit values (big endian) - THIS WAS THE BUG!
            self.ser.write(struct.pack('>HH', y_start, y_end))  # 0, 319
            time.sleep(0.01)
            
            # Memory Write command
            self.ser.write(b"\x2C")  # RAMWR command
            time.sleep(0.01)
            
            # Send pixel data
            print(f"[LCD] Sending {len(rgb565_data)} bytes of pixel data...")
            chunk_size = 1024
            for i in range(0, len(rgb565_data), chunk_size):
                chunk = rgb565_data[i:i + chunk_size]
                self.ser.write(chunk)
                time.sleep(0.01)
            
            self.ser.flush()
            print(f"[LCD] Image sent with area setup")
            time.sleep(0.2)
            return True
            
        except Exception as e:
            print(f"[LCD] Error with area setup: {e}")
            return False

    def send_image_with_area_alternative(self, image):
        """Alternative method - manual byte construction"""
        try:
            print(f"[LCD] Converting image to RGB565...")
            rgb565_data = self.image_to_rgb565(image)
            
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            print(f"[LCD] Setting display area (alternative method)...")
            
            # Column Address Set - manual byte construction
            self.ser.write(b"\x2A")  # CASET command
            time.sleep(0.01)
            self.ser.write(bytes([0x00, 0x00]))      # X start (0) as 16-bit big endian
            self.ser.write(bytes([0x00, 0xEF]))      # X end (239) as 16-bit big endian
            time.sleep(0.01)
            
            # Page Address Set - manual byte construction  
            self.ser.write(b"\x2B")  # PASET command
            time.sleep(0.01)
            self.ser.write(bytes([0x00, 0x00]))      # Y start (0) as 16-bit big endian
            self.ser.write(bytes([0x01, 0x3F]))      # Y end (319) as 16-bit big endian (0x013F = 319)
            time.sleep(0.01)
            
            # Memory Write command
            self.ser.write(b"\x2C")  # RAMWR command
            time.sleep(0.01)
            
            # Send pixel data
            print(f"[LCD] Sending {len(rgb565_data)} bytes of pixel data...")
            chunk_size = 1024
            for i in range(0, len(rgb565_data), chunk_size):
                chunk = rgb565_data[i:i + chunk_size]
                self.ser.write(chunk)
                time.sleep(0.01)
            
            self.ser.flush()
            print(f"[LCD] Image sent with alternative area setup")
            time.sleep(0.2)
            return True
            
        except Exception as e:
            print(f"[LCD] Error with alternative area setup: {e}")
            return False

    def clear_screen(self, color=(0, 0, 0)):
        """Clear screen to solid color"""
        clear_img = Image.new('RGB', (self.width, self.height), color=color)
        return self.send_image_basic(clear_img)

    def send_image(self, image, use_bgr=False, baudrate=None):
        """Main send image method - tries multiple protocols"""
        # Ignore use_bgr parameter since we're using RGB565
        # Ignore baudrate since we set it in constructor
        
        print(f"[LCD] Sending image: {image.size} -> {self.width}x{self.height}")
        
        # Try with fixed display area setup first
        if self.send_image_with_area(image):
            return True
        
        print("[LCD] Fixed area setup failed, trying alternative method...")
        if self.send_image_with_area_alternative(image):
            return True
        
        print("[LCD] Area setup failed, trying basic protocol...")
        return self.send_image_basic(image)

    def test_overflow_diagnostic(self):
        """Test to diagnose the coordinate overflow issue"""
        print("\n[LCD] Diagnostic Test: Coordinate Overflow Detection")
        
        # Test with magenta background and white stripe at overflow boundary
        print("[LCD] Diagnostic: Magenta with white stripe at row 63")
        test_img = Image.new('RGB', (self.width, self.height), color=(255, 0, 255))  # Magenta
        pixels = test_img.load()
        
        # Draw white horizontal stripe around the overflow point (row 63)
        for x in range(self.width):
            for y in range(60, 67):  # Rows 60-66
                pixels[x, y] = (255, 255, 255)  # White stripe
        
        self.send_image(test_img)
        time.sleep(3)
        print("[LCD] Look for: White stripe where new data ends, old data below")
        
    def test_patterns(self):
        """Test with clear patterns to verify display"""
        print("\n[LCD] Testing display with patterns...")
        
        # Test 0: Clear screen first
        print("[LCD] Test 0: Clearing screen (black)")
        self.clear_screen((0, 0, 0))
        time.sleep(1)
        
        # Diagnostic test first
        self.test_overflow_diagnostic()
        
        # Test 1: Solid red
        print("[LCD] Test 1: Solid red")
        red_img = Image.new('RGB', (self.width, self.height), color=(255, 0, 0))
        self.send_image(red_img)
        time.sleep(2)
        
        # Test 2: Solid green  
        print("[LCD] Test 2: Solid green")
        green_img = Image.new('RGB', (self.width, self.height), color=(0, 255, 0))
        self.send_image(green_img)
        time.sleep(2)
        
        # Test 3: Solid blue
        print("[LCD] Test 3: Solid blue")
        blue_img = Image.new('RGB', (self.width, self.height), color=(0, 0, 255))
        self.send_image(blue_img)
        time.sleep(2)
        
        # Test 4: Vertical stripes
        print("[LCD] Test 4: Vertical red/blue stripes")
        stripe_img = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        pixels = stripe_img.load()
        for x in range(self.width):
            for y in range(self.height):
                if x < self.width // 2:
                    pixels[x, y] = (255, 0, 0)  # Red
                else:
                    pixels[x, y] = (0, 0, 255)  # Blue
        self.send_image(stripe_img)
        time.sleep(2)
        
        # Test 5: Corner colors
        print("[LCD] Test 5: Corner colors")
        corner_img = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        pixels = corner_img.load()
        mid_x, mid_y = self.width // 2, self.height // 2
        for x in range(self.width):
            for y in range(self.height):
                if x < mid_x and y < mid_y:
                    pixels[x, y] = (255, 0, 0)    # Top-left: Red
                elif x >= mid_x and y < mid_y:
                    pixels[x, y] = (0, 255, 0)    # Top-right: Green
                elif x < mid_x and y >= mid_y:
                    pixels[x, y] = (0, 0, 255)    # Bottom-left: Blue
                else:
                    pixels[x, y] = (255, 255, 0)  # Bottom-right: Yellow
        self.send_image(corner_img)
        
        print("[LCD] Pattern tests complete!")

    def close(self):
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
            print("[LCD] Connection closed")

# Test the corrected LCD helper
if __name__ == "__main__":
    print("🧪 Testing Fixed LCD Helper")
    
    lcd = LCDHelper("COM3", 9600, width=240, height=320)
    
    try:
        lcd.test_patterns()
    except KeyboardInterrupt:
        print("\n🛑 Test stopped")
    finally:
        lcd.close()