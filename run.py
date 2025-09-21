#!/usr/bin/env python3
"""
Development runner script for the AI Ride Booking System

This script provides various commands for running and managing the application
in development mode.
"""

import asyncio
import sys
import subprocess
from pathlib import Path

def run_dev_server():
    """Run the development server with hot reload"""
    print("🚀 Starting AI Ride Booking System (Development Mode)")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔧 Admin Panel: http://localhost:8000/")
    print("💾 Redis: localhost:6379")
    print("\n" + "="*50 + "\n")

    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", "info"
    ])

def run_tests():
    """Run the test suite"""
    print("🧪 Running tests...")
    subprocess.run([sys.executable, "-m", "pytest", "-v"])

def run_tests_with_coverage():
    """Run tests with coverage report"""
    print("🧪 Running tests with coverage...")
    subprocess.run([
        sys.executable, "-m", "pytest",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term",
        "-v"
    ])

def lint_code():
    """Run code linting"""
    print("🔍 Running code linting...")
    subprocess.run([sys.executable, "-m", "black", "app/", "main.py"])
    subprocess.run([sys.executable, "-m", "isort", "app/", "main.py"])
    subprocess.run([sys.executable, "-m", "flake8", "app/", "main.py"])

def check_types():
    """Run type checking"""
    print("🔍 Running type checking...")
    subprocess.run([sys.executable, "-m", "mypy", "app/"])

def setup_env():
    """Setup development environment"""
    print("⚙️ Setting up development environment...")

    # Check if .env exists
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from .env.example...")
        env_file.write_text(env_example.read_text())
        print("✅ .env file created. Please update it with your API keys.")

    # Install dependencies
    print("📦 Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    print("✅ Environment setup complete!")

def docker_build():
    """Build Docker image"""
    print("🐳 Building Docker image...")
    subprocess.run(["docker", "build", "-t", "ai-ride-booking", "."])

def docker_run():
    """Run Docker container"""
    print("🐳 Running Docker container...")
    subprocess.run([
        "docker", "run",
        "-p", "8000:8000",
        "--env-file", ".env",
        "ai-ride-booking"
    ])

def docker_compose_up():
    """Start services with Docker Compose"""
    print("🐳 Starting services with Docker Compose...")
    subprocess.run(["docker-compose", "up", "-d"])

def docker_compose_down():
    """Stop services with Docker Compose"""
    print("🐳 Stopping services with Docker Compose...")
    subprocess.run(["docker-compose", "down"])

def show_help():
    """Show help information"""
    print("""
🤖 AI Ride Booking System - Development Commands

Available commands:
  dev         - Run development server with hot reload
  test        - Run test suite
  test-cov    - Run tests with coverage report
  lint        - Run code linting (black, isort, flake8)
  typecheck   - Run type checking with mypy
  setup       - Setup development environment

Docker commands:
  docker-build   - Build Docker image
  docker-run     - Run Docker container
  compose-up     - Start services with Docker Compose
  compose-down   - Stop services with Docker Compose

Examples:
  python run.py dev          # Start development server
  python run.py test         # Run tests
  python run.py setup        # Setup environment
  python run.py compose-up   # Start with Docker Compose

For production deployment, use:
  docker-compose -f deployment/docker-compose.prod.yml up -d
""")

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()

    commands = {
        'dev': run_dev_server,
        'test': run_tests,
        'test-cov': run_tests_with_coverage,
        'lint': lint_code,
        'typecheck': check_types,
        'setup': setup_env,
        'docker-build': docker_build,
        'docker-run': docker_run,
        'compose-up': docker_compose_up,
        'compose-down': docker_compose_down,
        'help': show_help,
        '--help': show_help,
        '-h': show_help,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()