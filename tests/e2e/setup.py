"""
Quick setup script for Playwright E2E tests.

This script installs all necessary dependencies for running the
end-to-end walkthrough tests.
"""
import subprocess
import sys


def run_command(command, description):
    """Run a command and print status."""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(e.stderr)
        return False


def main():
    """Setup Playwright testing environment."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║  Playwright E2E Test Setup                                 ║
║  This will install Playwright and browser dependencies     ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Install Python packages
    success = run_command(
        f"{sys.executable} -m pip install -r tests/e2e/requirements.txt",
        "Installing Python packages (playwright, pytest)"
    )
    
    if not success:
        print("\n❌ Failed to install Python packages")
        return 1
    
    # Step 2: Install Playwright browsers
    success = run_command(
        "playwright install chromium",
        "Installing Chromium browser"
    )
    
    if not success:
        print("\n⚠️  Warning: Browser installation failed")
        print("You may need to run: playwright install chromium")
        return 1
    
    # Success summary
    print("\n" + "="*60)
    print("🎉 Setup complete!")
    print("="*60)
    print("\n✅ Ready to run tests:")
    print("   python tests/e2e/test_walkthrough.py")
    print("\n📝 Make sure the server is running first:")
    print("   python -m src.main")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
