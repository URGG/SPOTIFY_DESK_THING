"""
Quick test to verify setup is working
Run this after setting up your .env file
"""

import os
import sys

def test_setup():
    print("🧪 Testing Spotify Display Setup...")
    
    # Test 1: Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("   Create a .env file with your Spotify credentials")
        return False
    print("✅ .env file found")
    
    # Test 2: Try to load configuration
    try:
        sys.path.append('src')
        from config_loader import load_config
        config = load_config()
        print("✅ Configuration loaded successfully")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("   Make sure your .env file has valid Spotify credentials")
        return False
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    # Test 3: Check if dependencies are installed
    try:
        import spotipy
        import flask
        from dotenv import load_dotenv
        print("✅ All dependencies installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    # Test 4: Try creating Spotify client
    try:
        from spotify_client import SpotifyClient
        client = SpotifyClient(
            config.SPOTIFY_CLIENT_ID,
            config.SPOTIFY_CLIENT_SECRET, 
            config.SPOTIFY_REDIRECT_URI
        )
        print("✅ Spotify client created (authentication will happen on first run)")
    except Exception as e:
        print(f"❌ Spotify client error: {e}")
        return False
    
    print("\n🎉 Setup test passed!")
    print("Next step: Run 'python src/app.py' to start the application")
    return True

if __name__ == "__main__":
    success = test_setup()
    if not success:
        sys.exit(1)