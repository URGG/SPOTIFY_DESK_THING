#!/usr/bin/env python3
"""
Build script for creating Spotify Car Thing executable
======================================================

This script creates a standalone executable using PyInstaller.
Run this script to build the executable for distribution.

Usage:
    python build_exe.py

Requirements:
    pip install pyinstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} found")
        return True
    except ImportError:
        print("❌ PyInstaller not found. Please install it:")
        print("   pip install pyinstaller")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        ('spotipy', 'spotipy'),
        ('pillow', 'PIL'),  # pillow installs as PIL
        ('requests', 'requests'), 
        ('psutil', 'psutil')
    ]
    
    missing = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} found")
        except ImportError:
            missing.append(package_name)
            print(f"❌ {package_name} not found")
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Install them with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True

def detect_scripts():
    """Detect the location of main script and client script"""
    main_script = None
    client_script = None
    
    if Path('spotify_car_thing.py').exists():
        main_script = 'spotify_car_thing.py'
        client_script = 'spotify_client.py' if Path('spotify_client.py').exists() else None
    elif Path('src/spotify_car_thing.py').exists():
        main_script = 'src/spotify_car_thing.py'
        client_script = 'src/spotify_client.py' if Path('src/spotify_client.py').exists() else None
        print("📁 Found scripts in src/ directory")
    else:
        return None, None
    
    return main_script, client_script

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"🧹 Cleaning {dir_name}/")
            shutil.rmtree(dir_name)

def create_spec_file(main_script, client_script):
    """Create PyInstaller spec file with custom configuration"""
    
    # Prepare data files list
    datas = []
    if Path('README.md').exists():
        datas.append("('README.md', '.')")
    if Path('requirements.txt').exists():
        datas.append("('requirements.txt', '.')")
    if client_script:
        datas.append(f"('{client_script}', '.')")
    
    # Add turing library if it exists
    turing_path = Path('turing-smart-screen-python-main')
    if turing_path.exists():
        datas.append(f"('{turing_path}', 'turing-smart-screen-python-main')")
        print("📁 Including turing-smart-screen-python-main library")
    
    datas_str = ',\n        '.join(datas) if datas else ''
    
    # Check for optional files
    icon_file = 'spotify_icon.ico' if Path('spotify_icon.ico').exists() else None
    version_file = 'version_info.txt' if Path('version_info.txt').exists() else None
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Analysis of the main script
a = Analysis(
    ['{main_script}'],
    pathex=[],
    binaries=[],
    datas=[
        {datas_str}
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'requests.packages.urllib3',
        'spotify_client',
        'spotipy',
        'spotipy.util',
        'spotipy.oauth2',
        'spotipy.client',
        'psutil',
        'urllib3',
        'certifi',
        'library',
        'library.lcd',
        'library.lcd.lcd_comm',
        'library.lcd.lcd_comm_rev_a',
        'library.lcd.lcd_comm_rev_b',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'logging',
        'logging.handlers',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Process collected files
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SpotifyCarThing',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # This makes it run without a console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={repr(icon_file)},
    version={repr(version_file)},
)
'''
    
    with open('spotify_car_thing.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("📝 Created PyInstaller spec file with spotipy dependencies")

def create_version_info():
    """Create version info file for Windows executable"""
    
    version_info = '''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(4, 0, 0, 0),
    prodvers=(4, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Spotify Car Thing'),
         StringStruct(u'FileDescription', u'Professional Spotify Display for Car LCD Screens'),
         StringStruct(u'FileVersion', u'4.0.0.0'),
         StringStruct(u'InternalName', u'spotify_car_thing'),
         StringStruct(u'LegalCopyright', u'Copyright © 2024'),
         StringStruct(u'OriginalFilename', u'SpotifyCarThing.exe'),
         StringStruct(u'ProductName', u'Spotify Car Thing'),
         StringStruct(u'ProductVersion', u'4.0.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    print("📝 Created version info file")

def build_executable():
    """Build the executable using PyInstaller"""
    
    print("🔨 Building executable...")
    print("This may take several minutes...")
    
    # Build command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'spotify_car_thing.spec'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with return code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def create_distribution_package():
    """Create a distribution package with all necessary files"""
    
    if not Path('dist/SpotifyCarThing.exe').exists():
        print("❌ Executable not found in dist/ directory")
        return False
    
    # Create distribution directory
    dist_dir = Path('SpotifyCarThing_v4.0.0')
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    dist_dir.mkdir()
    
    # Copy executable
    shutil.copy('dist/SpotifyCarThing.exe', dist_dir / 'SpotifyCarThing.exe')
    
    # Copy documentation
    files_to_copy = [
        'README.md',
        'requirements.txt',
        'spotify_client.py'
    ]
    
    for file_name in files_to_copy:
        if Path(file_name).exists():
            shutil.copy(file_name, dist_dir / file_name)
    
    # Create installation instructions
    install_instructions = """# Spotify Car Thing v4.0.0 - Installation Guide

## Quick Start

1. **First Time Setup:**
   - Run `SpotifyCarThing.exe` 
   - Follow the Spotify authentication prompts
   - Connect your Turing Smart Screen LCD via USB

2. **Requirements:**
   - Spotify Premium account
   - Turing Smart Screen LCD display
   - Windows 10+ (or compatible system)
   - Active internet connection

3. **Usage:**
   - Start Spotify and play music
   - Run `SpotifyCarThing.exe`
   - The display will show current track information
   - Press Ctrl+C to exit safely

## Troubleshooting

If you get "spotipy not found" error:
- This shouldn't happen with the standalone exe
- If it does, install: pip install spotipy

If the display doesn't work:
1. Check USB connection to LCD
2. Ensure Spotify is running with music playing
3. Verify internet connection
4. Check the log file for error details

## Files Included

- `SpotifyCarThing.exe` - Main application (includes all dependencies)
- `spotify_client.py` - Spotify API client (for reference)
- `README.md` - Full documentation
- `requirements.txt` - Python dependencies (for developers)

## Support

For issues and support, please refer to the README.md file
or visit the project repository.

Happy listening! 🎵
"""
    
    with open(dist_dir / 'INSTALL.txt', 'w', encoding='utf-8') as f:
        f.write(install_instructions)
    
    # Create batch file for easy launching
    batch_content = """@echo off
title Spotify Car Thing
echo Starting Spotify Car Thing...
echo.
echo Make sure:
echo - Spotify is running with music playing
echo - LCD display is connected via USB
echo - You have completed first-time setup
echo.
pause
SpotifyCarThing.exe
pause
"""
    
    with open(dist_dir / 'Launch_SpotifyCarThing.bat', 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print(f"📦 Created distribution package: {dist_dir}/")
    
    # Create ZIP archive
    try:
        import zipfile
        zip_path = f"{dist_dir}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in dist_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(dist_dir.parent)
                    zipf.write(file_path, arcname)
        
        print(f"📦 Created ZIP package: {zip_path}")
        
        # Show package size
        zip_size = Path(zip_path).stat().st_size / (1024 * 1024)  # MB
        print(f"📊 Package size: {zip_size:.1f} MB")
        
    except ImportError:
        print("⚠️  Could not create ZIP package (zipfile not available)")
    
    return True

def cleanup_build_files():
    """Clean up temporary build files"""
    
    temp_files = [
        'spotify_car_thing.spec',
        'version_info.txt',
    ]
    
    temp_dirs = [
        'build',
        '__pycache__',
    ]
    
    print("🧹 Cleaning up temporary files...")
    
    for file_name in temp_files:
        if Path(file_name).exists():
            Path(file_name).unlink()
    
    for dir_name in temp_dirs:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)

def print_success_message():
    """Print success message with instructions"""
    
    success_msg = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                               BUILD SUCCESSFUL!                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

🎉 Your Spotify Car Thing executable has been created successfully!

📁 Files created:
   • SpotifyCarThing_v4.0.0/ - Distribution folder
   • SpotifyCarThing_v4.0.0.zip - Ready-to-share package
   • dist/SpotifyCarThing.exe - Standalone executable with ALL dependencies

🚀 To distribute your application:
   1. Share the SpotifyCarThing_v4.0.0.zip file
   2. Recipients can unzip and run SpotifyCarThing.exe
   3. No Python installation required on target machines!
   4. All dependencies (including spotipy) are bundled!

📋 Next Steps:
   • Test the executable on different systems
   • The exe now includes spotipy and all other dependencies
   • Users no longer need to install Python packages
   • Authentication still happens on first run

💡 Pro Tips:
   • The executable is now completely self-contained
   • All Python dependencies are bundled inside
   • Test on a machine without Python to verify it works
   • Consider creating a setup wizard for authentication

Ready for professional distribution! 🎵🚗
    """
    
    print(success_msg)

def main():
    """Main build process"""
    
    print("🔨 Spotify Car Thing - Executable Builder v4.1.0")
    print("=" * 60)
    
    # Check prerequisites
    if not check_pyinstaller():
        return 1
    
    print("⚠️  Skipping dependency check - proceeding with build...")
    print("If build fails, install missing packages manually")
    
    # Detect script locations
    main_script, client_script = detect_scripts()
    
    if not main_script:
        print("❌ spotify_car_thing.py not found in current directory or src/ subdirectory")
        return 1
    
    if not client_script:
        print("⚠️  spotify_client.py not found - users will need to provide this")
    
    print(f"📋 Main script: {main_script}")
    if client_script:
        print(f"📋 Client script: {client_script}")
    
    # Build process
    try:
        print("\n🏗️  Starting build process...")
        
        clean_build_dirs()
        create_version_info()
        create_spec_file(main_script, client_script)
        
        if not build_executable():
            return 1
        
        if not create_distribution_package():
            return 1
        
        cleanup_build_files()
        print_success_message()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Build cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Build failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)