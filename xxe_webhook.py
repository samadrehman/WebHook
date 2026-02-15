# XXE WEBHOOK CATCHER - PYTHON BACKEND
# Deploy to Railway.app for free webhook catching
# Author: Built for Samad Rehman

from flask import Flask, request, render_template_string
from datetime import datetime
import json
import os

app = Flask(__name__)

# Store all incoming requests in memory
requests_log = []

# HTML template for viewing requests
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>XXE Webhook Catcher</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #1a1a1a;
            color: #fff;
        }
        h1 {
            color: #00ff00;
            text-align: center;
        }
        .stats {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .stat-item {
            display: inline-block;
            margin: 0 20px;
            font-size: 18px;
        }
        .stat-value {
            color: #00ff00;
            font-weight: bold;
            font-size: 24px;
        }
        .request {
            background: #2a2a2a;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #00ff00;
            border-radius: 4px;
        }
        .request.xxe {
            border-left: 4px solid #ff0000;
            background: #3a1a1a;
        }
        .timestamp {
            color: #888;
            font-size: 12px;
        }
        .method {
            display: inline-block;
            padding: 4px 8px;
            background: #444;
            border-radius: 3px;
            font-weight: bold;
            margin-right: 10px;
        }
        .method.POST { background: #ff6b00; }
        .method.GET { background: #0066ff; }
        .path {
            color: #00ff00;
            font-weight: bold;
            font-size: 16px;
        }
        .headers, .body, .params {
            background: #1a1a1a;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            overflow-x: auto;
        }
        .label {
            color: #00ff00;
            font-weight: bold;
            margin-top: 10px;
        }
        .alert {
            background: #ff0000;
            color: #fff;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            font-weight: bold;
            text-align: center;
            font-size: 20px;
        }
        .ip {
            color: #ffaa00;
            font-weight: bold;
        }
        .clear-btn {
            background: #ff0000;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            float: right;
        }
        .clear-btn:hover {
            background: #cc0000;
        }
        pre {
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
    </style>
</head>
<body>
    <h1>🔥 XXE WEBHOOK CATCHER 🔥</h1>
    
    <div class="stats">
        <div class="stat-item">
            <div>Total Requests</div>
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
    </div>
    {% endif %}
    
    <h2>Recent Requests (Auto-refresh every 5s)</h2>
    
    {% for req in requests %}
    <div class="request {% if req.is_xxe %}xxe{% endif %}">
        <div class="timestamp">{{ req.timestamp }}</div>
        <div>
            <span class="method {{ req.method }}">{{ req.method }}</span>
            <span class="path">{{ req.path }}</span>
            {% if req.is_xxe %}
            <span style="color: #ff0000; font-weight: bold; margin-left: 10px;">⚠️ POSSIBLE XXE!</span>
            {% endif %}
        </div>
        
        <div class="label">Source IP:</div>
        <div class="ip">{{ req.ip }}</div>
        
        {% if req.headers %}
        <div class="label">Headers:</div>
        <div class="headers"><pre>{{ req.headers }}</pre></div>
        {% endif %}
        
        {% if req.params %}
        <div class="label">Query Parameters:</div>
        <div class="params"><pre>{{ req.params }}</pre></div>
        {% endif %}
        
        {% if req.body %}
        <div class="label">Body:</div>
        <div class="body"><pre>{{ req.body }}</pre></div>
        {% endif %}
    </div>
    {% endfor %}
    
    {% if not requests %}
    <div style="text-align: center; color: #888; padding: 40px;">
        <h2>No requests yet...</h2>
        <p>Waiting for XXE callbacks...</p>
        <p>Your webhook URL: <span style="color: #00ff00;">{{ webhook_url }}</span></p>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    """Display all caught requests"""
    xxe_count = sum(1 for r in requests_log if r.get('is_xxe'))
    last_request = requests_log[0]['timestamp'] if requests_log else 'Never'
    
    # Get webhook URL
    webhook_url = request.url_root
    
    return render_template_string(
        HTML_TEMPLATE,
        requests=requests_log,
        total_requests=len(requests_log),
        xxe_count=xxe_count,
        last_request=last_request,
        webhook_url=webhook_url
    )

@app.route('/clear', methods=['POST'])
def clear():
    """Clear all requests"""
    global requests_log
    requests_log = []
    return '<script>window.location="/"</script>'

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def catch_all(path):
    """Catch all incoming requests"""
    
    # Detect if this might be XXE
    is_xxe = False
    xxe_indicators = ['xml', 'dtd', 'entity', 'xxe', 'etc', 'passwd', 'hostname']
    
    # Check path
    for indicator in xxe_indicators:
        if indicator in path.lower():
            is_xxe = True
            break
    
    # Check user-agent
    user_agent = request.headers.get('User-Agent', '').lower()
    if 'java' in user_agent or 'xml' in user_agent or 'apache' in user_agent:
        is_xxe = True
    
    # Get request data
    req_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'method': request.method,
        'path': f'/{path}',
        'ip': request.headers.get('X-Forwarded-For', request.remote_addr),
        'headers': '\n'.join([f'{k}: {v}' for k, v in request.headers.items()]),
        'params': json.dumps(dict(request.args), indent=2) if request.args else None,
        'body': request.get_data(as_text=True) if request.get_data() else None,
        'is_xxe': is_xxe
    }
    
    # Add to log (keep last 50 requests)
    requests_log.insert(0, req_data)
    if len(requests_log) > 50:
        requests_log.pop()
    
    # Print to console
    print(f"\n{'='*60}")
    print(f"🔔 NEW REQUEST: {request.method} /{path}")
    if is_xxe:
        print(f"🚨 POTENTIAL XXE DETECTED!")
    print(f"IP: {req_data['ip']}")
    print(f"Time: {req_data['timestamp']}")
    if req_data['body']:
        print(f"Body: {req_data['body'][:200]}")
    print(f"{'='*60}\n")
    
    # Return success
    return {
        'status': 'success',
        'message': 'Request logged',
        'timestamp': req_data['timestamp'],
        'xxe_detected': is_xxe
    }, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)