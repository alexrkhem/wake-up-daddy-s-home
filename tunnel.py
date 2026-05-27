"""
tunnel.py — Expose dashboard to your phone via ngrok
Run: python tunnel.py
Then open the URL on your phone browser.
"""
import subprocess, sys, time, os
from dotenv import load_dotenv
load_dotenv()

PORT    = 8501
NGROK_TOKEN = os.getenv("NGROK_AUTH_TOKEN", "")

def run():
    print("\n🎵  Jarvis Dashboard — Phone Tunnel")
    print("=" * 45)

    if not NGROK_TOKEN:
        print("\n⚠  No NGROK_AUTH_TOKEN in .env")
        print("   1. Sign up free at https://ngrok.com")
        print("   2. Copy your auth token")
        print("   3. Add to .env:  NGROK_AUTH_TOKEN=your-token")
        print("\n   Then re-run: python tunnel.py\n")
        sys.exit(1)

    try:
        from pyngrok import ngrok, conf
        conf.get_default().auth_token = NGROK_TOKEN

        # Start Streamlit in background
        print(f"▶  Starting Streamlit on port {PORT}…")
        streamlit_proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py",
             "--server.port", str(PORT),
             "--server.headless", "true",
             "--server.address", "0.0.0.0"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(3)

        # Open ngrok tunnel
        print("🌐  Opening ngrok tunnel…")
        tunnel = ngrok.connect(PORT, "http")
        public_url = tunnel.public_url

        print(f"\n✅  Dashboard is live!")
        print(f"\n   📱  Phone URL:  {public_url}")
        print(f"   💻  Local URL:  http://localhost:{PORT}")
        print(f"\n   Open the Phone URL in any browser on your phone.")
        print(f"   Bookmark it for easy access.\n")
        print("   Press Ctrl+C to stop.\n")

        try:
            streamlit_proc.wait()
        except KeyboardInterrupt:
            print("\n🛑  Shutting down…")
            ngrok.kill()
            streamlit_proc.terminate()

    except ImportError:
        print("⚠  pyngrok not installed. Run: pip install pyngrok")
        sys.exit(1)
    except Exception as e:
        print(f"❌  Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
