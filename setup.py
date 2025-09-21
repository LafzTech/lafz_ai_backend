#!/usr/bin/env python3
"""
Setup script for AI Ride Booking System

This script handles installation and setup of the application.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_system_dependencies():
    """Install system dependencies for audio processing"""
    print("📦 Installing system dependencies...")

    try:
        # Check if we're in a container or have apt available
        if os.path.exists('/usr/bin/apt-get'):
            subprocess.run([
                'sudo', 'apt-get', 'update', '&&',
                'sudo', 'apt-get', 'install', '-y',
                'ffmpeg', 'libsndfile1', 'libsndfile1-dev'
            ], shell=True, check=True)
            print("✅ System dependencies installed")
        else:
            print("⚠️  System dependencies may need to be installed manually:")
            print("   - ffmpeg (for audio processing)")
            print("   - libsndfile1 (for audio file support)")
    except subprocess.CalledProcessError:
        print("⚠️  Could not install system dependencies automatically")
        print("   Please install manually: ffmpeg, libsndfile1")

def install_python_dependencies():
    """Install Python dependencies"""
    print("🐍 Installing Python dependencies...")

    try:
        # Upgrade pip first
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
        ], check=True)

        # Install core requirements
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True)

        print("✅ Core dependencies installed")

        # Ask if user wants development dependencies
        install_dev = input("Install development dependencies? (y/N): ").lower().startswith('y')
        if install_dev:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements-dev.txt'
            ], check=True)
            print("✅ Development dependencies installed")

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        sys.exit(1)

def setup_environment():
    """Setup environment configuration"""
    print("⚙️ Setting up environment...")

    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text())
        print("📝 Created .env file from .env.example")
        print("⚠️  Please update .env with your API keys before running the application")
    elif env_file.exists():
        print("📝 .env file already exists")
    else:
        print("⚠️  No .env.example file found")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")

    directories = [
        "logs",
        "tmp/audio",
        "tmp/uploads",
        "tests",
        "docs"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    print("✅ Directories created")

def setup_git_hooks():
    """Setup git pre-commit hooks"""
    if Path(".git").exists():
        try:
            subprocess.run([
                sys.executable, '-m', 'pre_commit', 'install'
            ], check=True)
            print("✅ Git hooks installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Pre-commit hooks not installed (pre-commit not available)")

def main():
    """Main setup function"""
    print("🚀 AI Ride Booking System Setup")
    print("=" * 40)

    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required")
        sys.exit(1)

    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

    # Run setup steps
    create_directories()
    setup_environment()

    # Ask for system dependencies
    install_sys = input("Install system dependencies? (requires sudo) (y/N): ").lower().startswith('y')
    if install_sys:
        install_system_dependencies()

    install_python_dependencies()
    setup_git_hooks()

    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Update your .env file with API keys")
    print("2. Start Redis: docker run -d -p 6379:6379 redis:7-alpine")
    print("3. Run the application: python run.py dev")
    print("4. Visit http://localhost:8000/docs for API documentation")

if __name__ == "__main__":
    main()