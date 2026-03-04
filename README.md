Smart Webhook Listener with Railway Health-Check Filtering
Built for security researchers and penetration testers to capture real XXE callbacks without noise from Railway health checks.

📌 Overview

XXE Webhook Catcher V2 is a lightweight Flask-based webhook listener designed to:
Capture real external callbacks
Filter out Railway health checks & monitoring pings
Detect potential XXE attempts
Provide a clean web dashboard
Log request metadata for security analysis

Perfect for:
XXE vulnerability testing
Out-of-band interaction detection
Security lab environments
Bug bounty research

 Features
✅ Filters Railway health pings automatically
✅ Filters /health, /ping, /status, /favicon etc
✅ Logs only real external requests
✅ Detects potential XXE indicators
✅ Clean live dashboard (auto refresh every 3s)
✅ Keeps last 20 real requests
✅ Console logging for Railway logs
✅ One-click clear logs

🖥 Dashboard Preview
The dashboard displays:
Webhook URL
Total real requests
Potential XXE detections
Last request timestamp
Table of recent requests

Each request shows:
Time
HTTP Method
Path
IP Address
XXE Status (Normal / Possible XXE)



## File System 
Procfile : setup for railway if you want to deploy on railway 
xxe_webhook_v2.py = main file 
requirements.txt = download all requirement for use 
