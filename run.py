import os
import sys
import time
import webbrowser
import uvicorn

def main():
    print("=" * 65)
    print(" KAIROS V2: Autonomous Ocean Intelligence System")
    print(" Starting Tactical Core Backend on http://localhost:8000...")
    print("=" * 65)

    # Open browser automatically after 1.5s
    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://localhost:8000")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Launch Uvicorn server
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
