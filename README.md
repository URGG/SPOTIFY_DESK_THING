# 🎵 Spotify Car Display

A professional Spotify display interface designed for car LCD screens. Features real-time track information, album artwork, and seamless integration with your vehicle's display system.

![Version](https://img.shields.io/badge/version-4.0.0-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.7%2B-blue)

## ✨ Features

- **Real-time Track Display**: Shows current song, artist, album, and progress
- **Album Artwork**: Downloads and displays high-quality album covers
- **Professional Interface**: Spotify-inspired design with smooth animations
- **Smart Loading States**: Professional loading screens and error handling
- **Automatic Rotation**: Landscape interface optimized for portrait displays
- **Robust Error Recovery**: Automatic reconnection and state management
- **Memory Efficient**: Intelligent caching system for artwork and fonts

## 🖼️ Screenshots

*Real-time track display with album artwork and progress*
*Professional loading screens and error states*
*Clean, Spotify-inspired interface design*

## 🔧 Hardware Requirements

- **Display**: Turing Smart Screen LCD (Rev A, Rev B, or compatible)
- **Connection**: USB port for display communication
- **System**: Windows, macOS, or Linux with Python 3.7+

## 📋 Software Requirements

- **Spotify**: Premium account with active Spotify application
- **Python**: 3.7 or higher
- **Internet**: For Spotify API and album artwork downloads

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project
git clone <your-repo-url>
cd spotify-car-display

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Spotify Authentication

```bash
# Run the Spotify client setup (first time only)
python spotify_client.py
```

Follow the authentication prompts to connect your Spotify account.

### 3. Connect Hardware

1. Connect your Turing Smart Screen LCD via USB
2. Ensure drivers are installed and device is recognized
3. Place the `turing-smart-screen-python-main` library in the project folder

### 4. Run the Display

```bash
python spotify_car_display.py
```

The display will show:
- ✅ Professional startup sequence
- 🎵 Current playing track (if any)
- ⏸️ Idle screen when no music is playing
- 🔄 Automatic updates as music changes

### 5. Exit Safely

Press `Ctrl+C` at any time for a graceful shutdown.

## 📁 Project Structure

```
spotify-car-display/
├── spotify_car_display.py          # Main application
├── spotify_client.py               # Spotify API client (required)
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── LICENSE                         # MIT license
├── turing-smart-screen-python-main/ # LCD library (download separately)
└── logs/
    └── spotify_car_display.log     # Application logs
```

## ⚙️ Configuration

The application includes a `DisplayConfig` class for easy customization:

```python
@dataclass
class DisplayConfig:
    # Display dimensions
    logical_width: int = 480      # Design width (landscape)
    logical_height: int = 320     # Design height (landscape)
    
    # Layout settings
    album_art_size: int = 180     # Album artwork size
    margin: int = 20              # Screen margins
    
    # Font sizes
    title_font_size: int = 24     # Track title
    artist_font_size: int = 18    # Artist name
    album_font_size: int = 16     # Album name
    
    # Update settings
    update_interval: float = 1.0  # Seconds between updates
```

## 🎨 Color Scheme

Professional Spotify-inspired color palette:

- **Background**: `#121212` (Dark gray)
- **Primary Text**: `#FFFFFF` (White)
- **Secondary Text**: `#B3B3B3` (Light gray)
- **Spotify Green**: `#1ED760` (Brand accent)
- **Progress Background**: `#535353` (Medium gray)

## 🛠️ Advanced Features

### Loading States
- Professional startup sequence
- Real-time connection status
- Animated loading indicators
- Error recovery screens

### Memory Management
- Smart album artwork caching
- Font caching system
- Automatic cache cleanup
- Memory-efficient image processing

### Error Handling
- Automatic retry mechanisms
- Connection failure recovery
- Graceful degradation
- Comprehensive logging

## 📱 Display Modes

### Active Playback
- Album artwork (180x180px)
- Track title, artist, and album
- Real-time progress bar with timestamps
- Play/pause state indicator
- Spotify branding

### Idle Mode
- "No music playing" message
- Instructions to start Spotify
- Subtle Spotify branding
- Low-power display state

### Loading States
- Spotify logo with animations
- Connection status messages
- Progress indicators
- Professional error screens

## 🔍 Troubleshooting

### Display Not Working
1. Check USB connection to LCD
2. Verify LCD drivers are installed
3. Ensure `turing-smart-screen-python-main` library is present
4. Try different USB ports

### No Track Information
1. Ensure Spotify Premium account
2. Verify Spotify application is running
3. Check authentication status
4. Confirm internet connection

### Performance Issues
1. Check system resources
2. Reduce update frequency in config
3. Clear album art cache
4. Restart the application

##  Logging

The application creates detailed logs in `spotify_car_display.log`:

- Startup and shutdown events
- Track changes and progress updates
- Error conditions and recovery
- Performance metrics
- Debug information

Log levels:
- `INFO`: Normal operation events
- `WARNING`: Non-critical issues
- `ERROR`: Error conditions
- `DEBUG`: Detailed diagnostic info

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run code formatting
black spotify_car_display.py

# Run linting
pylint spotify_car_display.py

# Run type checking
mypy spotify_car_display.py
```

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Acknowledgments

- **Spotify**: For the excellent Web API and design inspiration
- **Turing Smart Screen**: For the LCD display hardware
- **Python Imaging Library (Pillow)**: For image processing capabilities
- **Requests Library**: For HTTP communication



For issues, questions, or contributions:

1. Check the troubleshooting section above
2. Review existing GitHub issues
3. Create a new issue with detailed information
4. Join the community discussions

---

**Made with ❤️ for car audio enthusiasts and Spotify lovers**