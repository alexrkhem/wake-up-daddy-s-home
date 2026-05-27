"""
setup.py — First-time setup for Jarvis Dashboard
Run: python setup.py
"""
import subprocess, sys, os, shutil
from pathlib import Path

def run():
    print("\n🎵  Jarvis Dashboard — First Time Setup")
    print("=" * 45)

    # 1. Check Python version
    if sys.version_info < (3, 9):
        print(f"❌  Python 3.9+ required (you have {sys.version})")
        sys.exit(1)
    print(f"✓  Python {sys.version_info.major}.{sys.version_info.minor}")

    # 2. Install requirements
    print("\n📦  Installing requirements…")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"],
        capture_output=False
    )
    if result.returncode != 0:
        print("⚠  Some packages may have failed. Check errors above.")
    else:
        print("✓  All packages installed")

    # 3. Create .env if it doesn't exist
    env_path = Path(".env")
    if not env_path.exists():
        shutil.copy(".env.example", ".env")
        print("\n📝  Created .env from template")
        print("   ⚡ Open .env and add your ANTHROPIC_API_KEY")
    else:
        print("\n✓  .env already exists")

    # 4. Initialize DB
    print("\n🗄  Initializing database…")
    sys.path.insert(0, str(Path(__file__).parent))
    from database import init_db
    init_db()
    print("✓  Database initialized with default data")

    # 5. Create directories
    from config import FILES_DIR, DATA_DIR, UPLOADS_DIR, PHOTOS_DIR
    for d, name in [(FILES_DIR,"Files"), (DATA_DIR,"Data"),
                    (UPLOADS_DIR,"Uploads"), (PHOTOS_DIR,"Photos")]:
        d.mkdir(parents=True, exist_ok=True)
        print(f"✓  {name} directory: {d}")

    print(f"""
╔══════════════════════════════════════════════════════╗
║  ✅  Setup complete! Here's how to run your dashboard:
║
║  1. Add your API key to .env:
║        ANTHROPIC_API_KEY=sk-ant-...
║
║  2. Start the dashboard:
║        Windows:  run.bat
║        Mac/Linux: ./run.sh
║        Or: streamlit run app.py
║
║  3. Access on phone:
║        Add NGROK_AUTH_TOKEN to .env, then:
║        python tunnel.py
║
║  4. Google Calendar setup:
║        See GOOGLE_CALENDAR_SETUP.md
╚══════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    run()
