"""
Script to run E2E tests with the server running.
This starts the FastAPI server, runs the Playwright tests, then stops the server.
"""
import subprocess
import time
import sys
import requests
from pathlib import Path


def is_server_running(url="http://localhost:8001/health"):
    """Check if the server is running."""
    try:
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except:
        return False


def run_e2e_tests():
    """Run E2E tests with server management."""
    print("=" * 70)
    print("Running E2E Tests for Artwork Detail Page")
    print("=" * 70)
    
    server_process = None
    server_was_running = is_server_running()
    
    try:
        if not server_was_running:
            print("\n🚀 Starting FastAPI server on port 8001...")
            server_process = subprocess.Popen(
                ["python", "-m", "uvicorn", "main:app", "--port", "8001"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            # Wait for server to start
            print("⏳ Waiting for server to start...")
            for i in range(30):  # Wait up to 30 seconds
                if is_server_running():
                    print("✅ Server is ready!")
                    break
                time.sleep(1)
            else:
                print("❌ Server failed to start within 30 seconds")
                return 1
        else:
            print("\n✅ Server is already running")
        
        # Run the tests
        print("\n" + "=" * 70)
        print("Running Playwright E2E Tests")
        print("=" * 70 + "\n")
        
        result = subprocess.run(
            [
                "python", "-m", "pytest",
                "tests/e2e/test_detail_page_ui.py",
                "-v"
            ],
            cwd=Path.cwd()
        )
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
        
    finally:
        # Clean up server if we started it
        if server_process and not server_was_running:
            print("\n🛑 Stopping server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("✅ Server stopped")


if __name__ == "__main__":
    sys.exit(run_e2e_tests())
