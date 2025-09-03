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
        self.width = 1024
        self.height = 600
        
    def connect(self):
        """Connect to the LCD display"""
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Give time for connection to stabilize
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
    
    def send_image(self, img):
        """Main image sending method - tries optimized RGB565 first, falls back to line-by-line"""
        if not self.connected or not self.ser:
            print("❌ Display not connected")
            return False
        
        # Try RGB565 method first (usually faster)
        success = self.send_image_rgb565_optimized(img)
        
        if success:
            return True
        
        # If RGB565 failed, try line-by-line method
        print("🔄 RGB565 failed, trying line-by-line method...")
        return self.send_image_line_by_line(img)
    
    def send_image_rgb565_optimized(self, img):
        """Optimized RGB565 method with better timing"""
        if not self.connected or not self.ser:
            print("❌ Display not connected")
            return False
        
        try:
            print("📤 Sending RGB565 format (optimized)")
            img_rgb = img.convert('RGB').resize((self.width, self.height))
            
            # Clear any existing buffer
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            # Send header with sync pattern
            header = bytearray()
            header.extend(b'\xFF\xFF\xFF\xFF')  # Sync pattern
            header.extend(b'\xAA\xBB')  # Start marker
            header.extend(self.width.to_bytes(2, byteorder='little'))
            header.extend(self.height.to_bytes(2, byteorder='little'))
            header.extend(b'\x01')  # RGB565 format flag
            
            self.ser.write(header)
            time.sleep(0.01)  # Small delay after header
            
            # Convert to RGB565 in chunks to avoid memory issues
            chunk_size = 1024  # Process 1024 pixels at a time
            pixels = list(img_rgb.getdata())
            
            for i in range(0, len(pixels), chunk_size):
                chunk = pixels[i:i + chunk_size]
                rgb565_chunk = bytearray()
                
                for r, g, b in chunk:
                    # Convert to RGB565 with proper bit shifting
                    r565 = (r & 0xF8) << 8   # 5 bits for red
                    g565 = (g & 0xFC) << 3   # 6 bits for green  
                    b565 = (b & 0xF8) >> 3   # 5 bits for blue
                    rgb565 = r565 | g565 | b565
                    
                    # Send as little endian
                    rgb565_chunk.extend(rgb565.to_bytes(2, byteorder='little'))
                
                self.ser.write(rgb565_chunk)
                time.sleep(0.001)  # Tiny delay between chunks
            
            # Send end marker
            self.ser.write(b'\xCC\xDD')
            print("✅ Image sent successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error sending image: {e}")
            return False
    
    def send_image_line_by_line(self, img):
        """Send image line by line - often more reliable"""
        if not self.connected or not self.ser:
            print("❌ Display not connected")
            return False
        
        try:
            print("📤 Sending line-by-line format")
            img_rgb = img.convert('RGB').resize((self.width, self.height))
            
            # Clear buffers
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            # Send header
            header = bytearray()
            header.extend(b'\xFF\xFF\xFF\xFF')  # Sync
            header.extend(b'\x12\x34')  # Line mode marker
            header.extend(self.width.to_bytes(2, byteorder='little'))
            header.extend(self.height.to_bytes(2, byteorder='little'))
            
            self.ser.write(header)
            time.sleep(0.01)
            
            # Send line by line
            for y in range(self.height):
                # Line header
                line_header = bytearray()
                line_header.extend(b'\xAA')  # Line start marker
                line_header.extend(y.to_bytes(2, byteorder='little'))
                line_header.extend(self.width.to_bytes(2, byteorder='little'))
                
                self.ser.write(line_header)
                
                # Line data (RGB888)
                line_data = bytearray()
                for x in range(self.width):
                    pixel = img_rgb.getpixel((x, y))
                    line_data.extend(pixel)
                
                self.ser.write(line_data)
                
                # Small delay every 10 lines to prevent buffer overflow
                if y % 10 == 0:
                    time.sleep(0.001)
                    
            # End marker
            self.ser.write(b'\xBB\xCC')
            print("✅ Line-by-line sent successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error sending line-by-line: {e}")
            return False
    
    def create_simple_test_image(self, test_type="rectangles"):
        """Create simple test images for debugging"""
        img = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        if test_type == "rectangles":
            # Simple colored rectangles
            colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0)]
            rect_width = self.width // 2
            rect_height = self.height // 2
            
            positions = [(0, 0), (rect_width, 0), (0, rect_height), (rect_width, rect_height)]
            
            for i, (color, pos) in enumerate(zip(colors, positions)):
                x, y = pos
                draw.rectangle((x, y, x + rect_width, y + rect_height), fill=color)
        
        elif test_type == "gradient":
            # Horizontal gradient
            for x in range(self.width):
                color_val = int(255 * x / self.width)
                for y in range(self.height):
                    draw.point((x, y), fill=(color_val, color_val, color_val))
        
        elif test_type == "checkerboard":
            # Checkerboard pattern
            square_size = 32
            for x in range(0, self.width, square_size):
                for y in range(0, self.height, square_size):
                    if (x // square_size + y // square_size) % 2:
                        color = (255, 255, 255)
                    else:
                        color = (0, 0, 0)
                    draw.rectangle((x, y, x + square_size, y + square_size), fill=color)
        
        elif test_type == "stripes":
            # Vertical stripes
            stripe_width = 20
            colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
            
            for x in range(0, self.width, stripe_width):
                color = colors[(x // stripe_width) % len(colors)]
                draw.rectangle((x, 0, x + stripe_width, self.height), fill=color)
        
        return img
    
    def create_text_test_image(self, text="LCD TEST"):
        """Create image with text for testing"""
        img = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Try to load a font
        try:
            font_large = ImageFont.truetype("arial.ttf", 72)
            font_medium = ImageFont.truetype("arial.ttf", 36)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        
        # Background rectangle
        draw.rectangle((50, 50, self.width-50, self.height-50), fill=(50, 50, 50))
        
        # Title
        draw.text((100, 100), text, fill=(255, 255, 255), font=font_large)
        
        # Status info
        draw.text((100, 200), f"Resolution: {self.width}x{self.height}", fill=(150, 150, 150), font=font_medium)
        draw.text((100, 250), "RGB888 Format", fill=(150, 150, 150), font=font_medium)
        draw.text((100, 300), "Serial Connection", fill=(0, 255, 0), font=font_medium)
        
        # Color bars at bottom
        bar_height = 50
        colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
        bar_width = self.width // len(colors)
        
        for i, color in enumerate(colors):
            x1 = i * bar_width
            x2 = (i + 1) * bar_width
            draw.rectangle((x1, self.height - bar_height, x2, self.height), fill=color)
        
        return img

def progressive_test():
    """Progressive testing from simple to complex"""
    display = LCDDisplayController()
    
    if not display.connect():
        print("❌ Could not connect to display")
        return
    
    tests = [
        ("Solid Red", lambda: Image.new('RGB', (1024, 600), color=(255, 0, 0))),
        ("Solid Green", lambda: Image.new('RGB', (1024, 600), color=(0, 255, 0))),
        ("Solid Blue", lambda: Image.new('RGB', (1024, 600), color=(0, 0, 255))),
        ("Four Rectangles", lambda: display.create_simple_test_image("rectangles")),
        ("Vertical Stripes", lambda: display.create_simple_test_image("stripes")),
        ("Checkerboard", lambda: display.create_simple_test_image("checkerboard")),
        ("Text Test", lambda: display.create_text_test_image()),
        ("Gradient", lambda: display.create_simple_test_image("gradient")),
    ]
    
    for test_name, image_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        img = image_func()
        
        # Try RGB565 method first
        print("  Trying RGB565 method...")
        success1 = display.send_image_rgb565_optimized(img)
        
        response = input(f"  RGB565 - What do you see? (good/lines/nothing/other): ").lower()
        
        if response == "good":
            print(f"  ✅ RGB565 works for {test_name}")
            continue
        elif response in ["lines", "nothing", "other"]:
            print("  ❌ RGB565 failed, trying line-by-line...")
            
            # Try line-by-line method
            success2 = display.send_image_line_by_line(img)
            response2 = input(f"  Line-by-line - What do you see? (good/lines/nothing/other): ").lower()
            
            if response2 == "good":
                print(f"  ✅ Line-by-line works for {test_name}")
            else:
                print(f"  ❌ Both methods failed for {test_name}")
                print(f"    This suggests the issue starts at complexity level: {test_name}")
                
                user_continue = input("  Continue testing? (y/n): ").lower()
                if user_continue != 'y':
                    break
    
    display.disconnect()

def debug_data_transmission():
    """Debug the actual data being sent"""
    display = LCDDisplayController()
    
    if not display.connect():
        return
    
    # Create a very simple image - just 4 pixels
    print("🔍 Testing minimal data transmission...")
    
    # 2x2 pixel image
    simple_img = Image.new('RGB', (2, 2), color=(0, 0, 0))
    simple_img.putpixel((0, 0), (255, 0, 0))    # Red
    simple_img.putpixel((1, 0), (0, 255, 0))    # Green
    simple_img.putpixel((0, 1), (0, 0, 255))    # Blue  
    simple_img.putpixel((1, 1), (255, 255, 255)) # White
    
    # Scale it up to full resolution
    scaled_img = simple_img.resize((1024, 600), Image.NEAREST)
    
    print("Sending 2x2 pattern scaled up (should show 4 large colored squares)")
    display.send_image_rgb565_optimized(scaled_img)
    
    input("What do you see? This should be very simple data. Press Enter...")
    
    display.disconnect()

if __name__ == "__main__":
    print("🖥️  LCD Display Testing Suite")
    print("=" * 50)
    
    while True:
        print("\nChoose a test:")
        print("1. Progressive Test (recommended)")
        print("2. Debug Minimal Data")  
        print("3. Quick Color Test")
        print("4. Custom Port/Baud")
        print("5. Exit")
        
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == "1":
            progressive_test()
        elif choice == "2":
            debug_data_transmission()
        elif choice == "3":
            display = LCDDisplayController()
            if display.connect():
                img = display.create_simple_test_image("rectangles")
                display.send_image_rgb565_optimized(img)
                input("Check display and press Enter...")
                display.disconnect()
        elif choice == "4":
            port = input("Enter COM port (e.g., COM3): ").strip()
            baud = int(input("Enter baud rate (e.g., 115200): ").strip())
            display = LCDDisplayController(port, baud)
            # Run progressive test with custom settings
            if display.connect():
                img = display.create_simple_test_image("rectangles")
                display.send_image_rgb565_optimized(img)
                input("Check display and press Enter...")
                display.disconnect()
        elif choice == "5":
            break
        else:
            print("Invalid choice")
            
    print("👋 Testing complete!")