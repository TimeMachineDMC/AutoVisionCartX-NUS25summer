#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import os

def check_dependencies():
    required_packages = [
        'flask',
        'flask_cors', 
        'faster_whisper'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"{package} - installed")
        except ImportError:
            print(f"{package} - missing")
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies():
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def start_voice_api():
    print("\nStarting Voice API server...")
    try:
        from voice_order_api import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except ImportError as e:
        print(f"Failed to import voice_order_api: {e}")
        return False
    except Exception as e:
        print(f"Failed to start server: {e}")
        return False

def main():
    print("MyMarket Voice Order API Startup")
    print("=" * 40)

    if sys.version_info < (3, 7):
        print("Python 3.7 or higher is required")
        sys.exit(1)
    
    print(f"Python {sys.version.split()[0]} detected")

    print("\nChecking dependencies...")
    missing = check_dependencies()
    
    if missing:
        print(f"\n Missing packages: {', '.join(missing)}")
        choice = input("Do you want to install them now? (y/n): ").lower().strip()
        
        if choice == 'y':
            if not install_dependencies():
                print("Installation failed. Please install manually:")
                print("   pip install -r requirements.txt")
                sys.exit(1)
        else:
            print("Cannot start without required dependencies")
            sys.exit(1)


    print("\nAPI will be available at: http://localhost:5000")
    print("Voice order endpoint: http://localhost:5000/api/voice-order")
    print("Make sure to start this API before using voice ordering in the web interface")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 40)
    
    start_voice_api()

if __name__ == "__main__":
    main() 