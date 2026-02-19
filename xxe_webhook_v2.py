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
    <title>Webhook Dashboard</title>
    <meta http-equiv="refresh" content="3">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        body {
            margin: 0;
            font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
            background: #f5f7fa;
            color: #222;
        }

        header {
            background: #ffffff;
            padding: 16px 24px;
            border-bottom: 1px solid #e5e7eb;
            font-size: 20px;
            font-weight: 600;
        }

        .container {
            max-width: 1100px;
            margin: 20px auto;
            padding: 0 16px;
        }

        .stats {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }

        .stat {
            background: white;
            padding: 12px 16px;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            min-width: 160px;
        }

        .stat strong {
            display: block;
            font-size: 20px;
            margin-top: 4px;
        }

        .url-box {
            background: #fff;
            padding: 12px 16px;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            margin-bottom: 20px;
            font-family: monospace;
        }

        button {
            background: #ef4444;
            color: white;
            border: none;
            padding: 8px 14px;
            border-radius: 4px;
            cursor: pointer;
            float: right;
        }

        button:hover {
            background: #dc2626;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border: 1px solid #e5e7eb;
        }

        th, td {
            padding: 10px;
            border-bottom: 1px solid #e5e7eb;
            text-align: left;
            font-size: 14px;
        }

        th {
            background: #f9fafb;
            font-weight: 600;
        }

        .method {
            font-weight: bold;
        }

        .xxe {
            color: #dc2626;
            font-weight: bold;
        }

        .empty {
            text-align: center;
            padding: 30px;
            color: #777;
        }
    </style>
</head>

<body>

<header>Webhook Dashboard</header>

<div class="container">

    <div class="url-box">
        <strong>Webhook URL:</strong><br>
        {{ webhook_url }}
    </div>

    <div class="stats">
        <div class="stat">Total Requests<strong>{{ total_requests }}</strong></div>
        <div class="stat">Potential XXE<strong>{{ xxe_count }}</strong></div>
        <div class="stat">Last Request<strong>{{ last_request }}</strong></div>
    </div>

    <form action="/clear" method="POST">
        <button type="submit">Clear Logs</button>
    </form>

    <h3>Recent Requests</h3>

    {% if requests %}
    <table>
        <tr>
            <th>Time</th>
            <th>Method</th>
            <th>Path</th>
            <th>IP</th>
            <th>Status</th>
        </tr>
        {% for req in requests %}
        <tr>
            <td>{{ req.timestamp }}</td>
            <td class="method">{{ req.method }}</td>
            <td>{{ req.path }}</td>
            <td>{{ req.ip }}</td>
            <td>
                {% if req.is_xxe %}
                    <span class="xxe">Possible XXE</span>
                {% else %}
                    Normal
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
        <div class="empty">No requests received yet</div>
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