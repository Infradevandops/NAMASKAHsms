#!/usr/bin/env python3
"""Check server logs for wallet endpoint errors."""

import subprocess
import time
import requests

# Make a request to trigger the error
print("Making request to /wallet...")
try:
    response = requests.get(
        "http://127.0.0.1:8001/wallet",
        headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjhlNTQyMTctNTk2MC00Y2ViLThmM2ItZDkxOWJiZjNmMmU1IiwiZW1haWwiOiJhZG1pbkBuYW1hc2thaC5hcHAiLCJleHAiOjE3NzE0NDMxNDl9.1Hqoqr2DstxZNOcnaMFX16BFOk7tKWfCl9kzXLinLa0"}
    )
    print(f"Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

time.sleep(1)

# Check logs
print("\n" + "="*60)
print("Checking logs for errors...")
print("="*60)

result = subprocess.run(
    ["tail", "-100", "app.log"],
    capture_output=True,
    text=True
)

lines = result.stdout.split('\n')
for i, line in enumerate(lines):
    if 'error' in line.lower() or 'exception' in line.lower() or 'traceback' in line.lower():
        # Print context
        start = max(0, i-2)
        end = min(len(lines), i+10)
        print('\n'.join(lines[start:end]))
        break
