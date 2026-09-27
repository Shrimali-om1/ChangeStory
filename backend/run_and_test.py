"""
run_and_test.py — Starts uvicorn in a subprocess, waits for it to be ready,
runs the smoke tests, then kills the server.
"""
import subprocess
import sys
import time
import os

# Start uvicorn
server = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000", "--log-level", "warning"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# Wait for server to be ready (poll /health)
import urllib.request, urllib.error

deadline = time.time() + 15
ready = False
while time.time() < deadline:
    try:
        urllib.request.urlopen("http://localhost:8000/health", timeout=2)
        ready = True
        break
    except Exception:
        time.sleep(0.3)

if not ready:
    server.kill()
    out, err = server.communicate()
    print("SERVER FAILED TO START")
    print(err.decode()[-2000:])
    sys.exit(1)

print("Server ready.\n")

# Run smoke tests
result = subprocess.run(
    [sys.executable, "smoke_test.py"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
)

server.kill()
server.communicate()
sys.exit(result.returncode)
