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
    <title>XXE Webhook Monitor</title>
    <meta http-equiv="refresh" content="3">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            background: #f4f6f8;
            color: #333;
        }

        /* Header */
        .header {
            background: #ffffff;
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid #ddd;
        }

        h1 {
            margin: 0;
            font-size: 26px;
        }

        .subtitle {
            color: #777;
            font-size: 14px;
        }

        .container {
            max-width: 1100px;
            margin: 20px auto;
            padding: 0 15px;
        }

        /* Cards */
        .card {
            background: #ffffff;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #ddd;
            margin-bottom: 20px;
        }

        .webhook-url {
            text-align: center;
            font-size: 16px;
        }

        .url-text {
            font-family: monospace;
            background: #f1f1f1;
            padding: 8px 12px;
            border-radius: 4px;
            display: inline-block;
            margin-top: 10px;
        }

        /* Stats */
        .stats {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            gap: 10px;
        }

        .stat-box {
            flex: 1;
            min-width: 150px;
            background: #fafafa;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #ddd;
            text-align: center;
        }

        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c7be5;
        }

        /* Buttons */
        .clear-btn {
            background: #e5533d;
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 4px;
            cursor: pointer;
            float: right;
        }

        .clear-btn:hover {
            background: #c73c2b;
        }

        /* Requests */
        .request {
            border-left: 4px solid #2c7be5;
        }

        .request.xxe {
            border-left-color: #e5533d;
            background: #fff5f5;
        }

        .timestamp {
            color: #888;
            font-size: 13px;
        }

        .method {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 8px;
            color: white;
        }

        .method.GET { background: #2c7be5; }
        .method.POST { background: #28a745; }

        .path {
            font-weight: bold;
        }

        .label {
            margin-top: 10px;
            font-weight: bold;
            font-size: 13px;
        }

        .headers, .body {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #ddd;
            font-family: monospace;
            font-size: 12px;
            overflow-x: auto;
        }

        .alert {
            background: #ffe5e5;
            color: #a30000;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            font-weight: bold;
            border: 1px solid #ffb3b3;
        }

        .no-requests {
            text-align: center;
            color: #777;
            padding: 40px;
        }
    </style>
</head>

<body>

    <div class="header">
        <h1>XXE Webhook Monitor</h1>
        <div class="subtitle">Real callbacks only — health checks filtered</div>
    </div>

    <div class="container">

        <!-- Webhook URL -->
        <div class="card webhook-url">
            <div>Your Webhook URL</div>
            <div class="url-text">{{ webhook_url }}</div>
        </div>

        <!-- Stats -->
        <div class="card">
            <form action="/clear" method="POST">
                <button type="submit" class="clear-btn">Clear All</button>
            </form>

            <div class="stats">
                <div class="stat-box">
                    <div>Total Callbacks</div>
                    <div class="stat-value">{{ total_requests }}</div>
                </div>

                <div class="stat-box">
                    <div>Potential XXE</div>
                    <div class="stat-value">{{ xxe_count }}</div>
                </div>

                <div class="stat-box">
                    <div>Last Request</div>
                    <div class="stat-value">{{ last_request }}</div>
                </div>
            </div>
        </div>

        {% if xxe_count > 0 %}
        <div class="alert">
            ⚠️ {{ xxe_count }} potential XXE callback(s) detected
        </div>
        {% endif %}

        <h2>Recent Callbacks</h2>

        {% for req in requests %}
        <div class="card request {% if req.is_xxe %}xxe{% endif %}">
            <div class="timestamp">{{ req.timestamp }}</div>

            <div>
                <span class="method {{ req.method }}">{{ req.method }}</span>
                <span class="path">{{ req.path }}</span>
                {% if req.is_xxe %}
                    <strong style="color:#e5533d;">⚠ Possible XXE</strong>
                {% endif %}
            </div>

            <div class="label">Source IP</div>
            <div>{{ req.ip }}</div>

            <div class="label">User-Agent</div>
            <div>{{ req.user_agent }}</div>

            {% if req.headers %}
            <div class="label">Headers</div>
            <div class="headers"><pre>{{ req.headers }}</pre></div>
            {% endif %}

            {% if req.body %}
            <div class="label">Body</div>
            <div class="body"><pre>{{ req.body }}</pre></div>
            {% endif %}
        </div>
        {% endfor %}

        {% if not requests %}
        <div class="no-requests">
            <h3>No callbacks yet</h3>
            <p>Use your webhook URL in XXE payloads</p>
            <code>{{ webhook_url }}/test</code>
        </div>
        {% endif %}

    </div>

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
    xxe_indicators = ['xml', 'dtd', 'entity', 'xxe', '/etc/passwd', 'file://', 'hostname']

    
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