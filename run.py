"""Single-window launcher for Piano Performance Analyzer.

Starts backend + frontend in one terminal.  Ctrl+C kills both cleanly.

Usage:
    py -3.11 run.py
"""

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

BACKEND_URL = "http://localhost:8000/health"
FRONTEND_URL = "http://localhost:3000"

# ---------------------------------------------------------------------------
def wait_for_url(url: str, label: str, timeout: float = 60) -> bool:
    """Poll *url* until it returns HTTP 200, or *timeout* seconds elapse."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


def main() -> None:
    print("=" * 50)
    print("  Piano Performance Analyzer")
    print("=" * 50)
    print()

    # -- Start backend -------------------------------------------------------
    print("[1/2] Starting backend  (http://localhost:8000) ...")
    backend = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "0.0.0.0", "--port", "8000",
        ],
        cwd=str(BACKEND_DIR),
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
    )

    if not wait_for_url(BACKEND_URL, "backend"):
        print("ERROR: Backend did not start within 60 s.")
        # Print captured backend output to help diagnose the problem
        try:
            out, _ = backend.communicate(timeout=2)
            if out:
                print("--- Backend output ---")
                print(out.decode(errors="replace"))
                print("----------------------")
        except Exception:
            pass
        backend.kill()
        sys.exit(1)
    print("  Backend is ready.")

    # -- Start frontend ------------------------------------------------------
    print("[2/2] Starting frontend (http://localhost:3000) ...")
    # On Windows, npm is npm.cmd — subprocess needs shell=True to find it.
    frontend = subprocess.Popen(
        "npm run dev",
        cwd=str(FRONTEND_DIR),
        shell=True,
        stderr=subprocess.STDOUT,
        stdout=subprocess.DEVNULL,
    )

    if not wait_for_url(FRONTEND_URL, "frontend"):
        print("ERROR: Frontend did not start within 60 s.")
        backend.kill()
        frontend.kill()
        sys.exit(1)
    print("  Frontend is ready.")

    # -- All good ------------------------------------------------------------
    print()
    print("=" * 50)
    print("  Both servers are running!")
    print(f"  Open  {FRONTEND_URL}")
    print("  Press Ctrl+C to stop both.")
    print("=" * 50)

    try:
        # Sleep until Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

    # -- Cleanup -------------------------------------------------------------
    print("  Stopping frontend...")
    frontend.terminate()
    try:
        frontend.wait(timeout=5)
    except subprocess.TimeoutExpired:
        frontend.kill()

    print("  Stopping backend...")
    backend.terminate()
    try:
        backend.wait(timeout=5)
    except subprocess.TimeoutExpired:
        backend.kill()

    print("Done.")
    sys.exit(0)


if __name__ == "__main__":
    main()
