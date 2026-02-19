# XXE WEBHOOK CATCHER V2 - FILTERS RAILWAY PINGS
# Deploy to Railway.app - only shows REAL callbacks
# Author: Built for Samad Rehman

from flask import Flask, request, render_template_string
from datetime import datetime
import json
import os

app = Flask(__name__)

# Store ONLY real requests (not Railway pings)
real_requests = []

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>XXE Webhook - Real Callbacks Only</title>
    <meta http-equiv="refresh" content="3">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #0a0a0a;
            color: #00ff00;
        }
        h1 {
            color: #00ff00;
            text-align: center;
            text-shadow: 0 0 10px #00ff00;
        }
        .webhook-url {
            background: #1a1a1a;
            padding: 20px;
            border: 2px solid #00ff00;
            border-radius: 8px;
            text-align: center;
            margin: 20px 0;
            font-size: 18px;
        }
        .url-text {
            color: #ffff00;
            font-weight: bold;
            font-family: monospace;
        }
        .stats {
            background: #1a1a1a;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #00ff00;
        }
        .stat-item {
            display: inline-block;
            margin: 0 30px;
            font-size: 18px;
        }
        .stat-value {
            color: #ffff00;
            font-weight: bold;
            font-size: 28px;
        }
        .request {
            background: #1a1a1a;
            padding: 20px;
            margin: 20px 0;
            border-left: 5px solid #00ff00;
            border-radius: 4px;
            animation: slideIn 0.5s;
        }
        .request.xxe {
            border-left: 5px solid #ff0000;
            background: #2a0a0a;
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.3);
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .timestamp {
            color: #888;
            font-size: 14px;
        }
        .method {
            display: inline-block;
            padding: 5px 10px;
            background: #444;
            border-radius: 3px;
            font-weight: bold;
            margin-right: 10px;
        }
        .method.POST { background: #ff6b00; color: #fff; }
        .method.GET { background: #0066ff; color: #fff; }
        .path {
            color: #ffff00;
            font-weight: bold;
            font-size: 18px;
        }
        .ip {
            color: #ff6600;
            font-weight: bold;
            font-size: 16px;
        }
        .headers, .body {
            background: #0a0a0a;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
            border: 1px solid #333;
            font-family: monospace;
            font-size: 13px;
            overflow-x: auto;
        }
        .label {
            color: #00ff00;
            font-weight: bold;
            margin-top: 15px;
            font-size: 14px;
        }
        .alert {
            background: #ff0000;
            color: #fff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            font-weight: bold;
            text-align: center;
            font-size: 24px;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .no-requests {
            text-align: center;
            color: #666;
            padding: 60px;
            font-size: 18px;
        }
        pre {
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .clear-btn {
            background: #ff0000;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 4px;
            cursor: pointer;
            float: right;
            font-size: 16px;
        }
        .clear-btn:hover {
            background: #cc0000;
        }
    </style>
</head>
<body>
    <h1>🔥 XXE WEBHOOK CATCHER 🔥</h1>
    <h2 style="text-align: center; color: #888;">Real Callbacks Only - Railway Pings Filtered</h2>
    
    <div class="webhook-url">
        <div>Your Webhook URL (use this in XXE payloads):</div>
        <div class="url-text">{{ webhook_url }}</div>
    </div>
    
    <div class="stats">
        <div class="stat-item">
            <div>Real Callbacks</div>
            <div class="stat-value">{{ total_requests }}</div>
        </div>
        <div class="stat-item">
            <div>Potential XXE</div>
            <div class="stat-value">{{ xxe_count }}</div>
        </div>
        <div class="stat-item">
            <div>Last Request</div>
            <div class="stat-value">{{ last_request }}</div>
        </div>
        <form action="/clear" method="POST" style="display: inline;">
            <button type="submit" class="clear-btn">Clear All</button>
        </form>
    </div>
    
    {% if xxe_count > 0 %}
    <div class="alert">
        🚨 {{ xxe_count }} POTENTIAL XXE CALLBACK(S) DETECTED! 🚨
        <br>📸 SCREENSHOT THIS IMMEDIATELY!
    </div>
    {% endif %}
    
    <h2 style="color: #00ff00;">Recent Callbacks (Auto-refresh every 3s)</h2>
    
    {% for req in requests %}
    <div class="request {% if req.is_xxe %}xxe{% endif %}">
        <div class="timestamp">⏰ {{ req.timestamp }}</div>
        <div style="margin: 10px 0;">
            <span class="method {{ req.method }}">{{ req.method }}</span>
            <span class="path">{{ req.path }}</span>
            {% if req.is_xxe %}
            <span style="color: #ff0000; font-weight: bold; margin-left: 15px; font-size: 20px;">⚠️ POSSIBLE XXE!</span>
            {% endif %}
        </div>
        
        <div class="label">Source IP:</div>
        <div class="ip">🌐 {{ req.ip }}</div>
        
        <div class="label">User-Agent:</div>
        <div style="color: #ffaa00;">{{ req.user_agent }}</div>
        
        {% if req.headers %}
        <div class="label">Full Headers:</div>
        <div class="headers"><pre>{{ req.headers }}</pre></div>
        {% endif %}
        
        {% if req.body %}
        <div class="label">Request Body:</div>
        <div class="body"><pre>{{ req.body }}</pre></div>
        {% endif %}
    </div>
    {% endfor %}
    
    {% if not requests %}
    <div class="no-requests">
        <h2>👀 Waiting for XXE callbacks...</h2>
        <p>Use your webhook URL in XXE payloads</p>
        <p style="color: #00ff00; font-family: monospace;">{{ webhook_url }}/test</p>
        <br>
        <p style="color: #666; font-size: 14px;">Railway health checks are automatically filtered</p>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    """Display all caught requests"""
    xxe_count = sum(1 for r in real_requests if r.get('is_xxe'))
    last_request = real_requests[0]['timestamp'] if real_requests else 'Never'
    webhook_url = request.url_root.rstrip('/')
    
    return render_template_string(
        HTML_TEMPLATE,
        requests=real_requests,
        total_requests=len(real_requests),
        xxe_count=xxe_count,
        last_request=last_request,
        webhook_url=webhook_url
    )

@app.route('/clear', methods=['POST'])
def clear():
    """Clear all requests"""
    global real_requests
    real_requests = []
    return '<script>window.location="/"</script>'

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def catch_all(path):
    """Catch all incoming requests - FILTER RAILWAY PINGS"""
    
    # Get request info
    user_agent = request.headers.get('User-Agent', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # ═══════════════════════════════════════════════════════════
    # FILTER OUT RAILWAY AND HEALTH CHECKS
    # ═══════════════════════════════════════════════════════════
    
    # Filter Railway health checks
    if 'railway' in user_agent.lower():
        return {'status': 'ok'}, 200
    
    # Filter common health check paths
    if path.lower() in ['', 'health', 'ping', 'status', 'healthz', 'ready']:
        return {'status': 'ok'}, 200
    
    # Filter favicon requests
    if 'favicon' in path.lower():
        return '', 404
    
    # Filter requests from same IP as Railway (localhost/monitoring)
    if ip.startswith('127.') or ip.startswith('::1') or ip == 'localhost':
        return {'status': 'ok'}, 200
    
    # ═══════════════════════════════════════════════════════════
    # THIS IS A REAL REQUEST - LOG IT!
    # ═══════════════════════════════════════════════════════════
    
    # Detect if this might be XXE
    is_xxe = False
    xxe_indicators = ['xml', 'dtd', 'entity', 'xxe', 'etc', 'passwd', 'hostname', 
                      'test', 'zoho', 'razorpay', 'coindcx', 'freshworks']
    
    # Check path for XXE indicators
    for indicator in xxe_indicators:
        if indicator in path.lower():
            is_xxe = True
            break
    
    # Check user-agent (servers making XXE callbacks)
    ua_lower = user_agent.lower()
    if any(x in ua_lower for x in ['java', 'apache', 'python-urllib', 'okhttp', 'go-http']):
        is_xxe = True
    
    # Get request data
    req_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'method': request.method,
        'path': f'/{path}',
        'ip': ip,
        'user_agent': user_agent,
        'headers': '\n'.join([f'{k}: {v}' for k, v in request.headers.items()]),
        'body': request.get_data(as_text=True) if request.get_data() else None,
        'is_xxe': is_xxe
    }
    
    # Add to log (keep last 20 REAL requests only)
    real_requests.insert(0, req_data)
    if len(real_requests) > 20:
        real_requests.pop()
    
    # Print to console (Railway logs)
    print(f"\n{'='*60}")
    print(f"🔔 REAL REQUEST RECEIVED!")
    if is_xxe:
        print(f"🚨🚨🚨 POTENTIAL XXE DETECTED! 🚨🚨🚨")
    print(f"Method: {request.method}")
    print(f"Path: /{path}")
    print(f"IP: {ip}")
    print(f"User-Agent: {user_agent}")
    print(f"Time: {req_data['timestamp']}")
    if req_data['body']:
        print(f"Body: {req_data['body'][:200]}")
    print(f"{'='*60}\n")
    
    # Return success
    return {
        'status': 'logged',
        'message': 'Request captured',
        'timestamp': req_data['timestamp'],
        'xxe_detected': is_xxe
    }, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*60}")
    print(f"🔥 XXE WEBHOOK CATCHER STARTED")
    print(f"   Port: {port}")
    print(f"   Railway pings: FILTERED ✅")
    print(f"   Real callbacks: LOGGED ✅")
    print(f"{'='*60}\n")
    app.run(host='0.0.0.0', port=port, debug=False)