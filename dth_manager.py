import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, jsonify, Response
from prometheus_client import Counter, generate_latest, Gauge
import time

app = Flask(__name__)

# --- DevOps Metrics (Prometheus) ---
REQUEST_COUNT = Counter('dth_request_count', 'Total App Requests', ['method', 'endpoint'])
ACTIVE_SUBSCRIPTIONS = Gauge('dth_active_subs', 'Number of active subscriptions')
DB_CONNECTION_TIME = Gauge('dth_db_conn_time', 'Time taken to connect to DB')

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('dth.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscribers 
                 (id INTEGER PRIMARY KEY, name TEXT, package TEXT, status TEXT)''')
    # Seed some data if empty
    c.execute('SELECT count(*) FROM subscribers')
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO subscribers (name, package, status) VALUES ('John Doe', 'Sports Pack', 'Active')")
        c.execute("INSERT INTO subscribers (name, package, status) VALUES ('Jane Smith', 'Cinema Plus', 'Active')")
        conn.commit()
    conn.close()

# --- Routes ---

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    request_latency = time.time() - request.start_time
    REQUEST_COUNT.labels(request.method, request.path).inc()
    return response

@app.route('/')
def index():
    conn = sqlite3.connect('dth.db')
    c = conn.cursor()
    c.execute("SELECT * FROM subscribers")
    subs = c.fetchall()
    
    # Update metric
    c.execute("SELECT count(*) FROM subscribers WHERE status='Active'")
    active_count = c.fetchone()[0]
    ACTIVE_SUBSCRIPTIONS.set(active_count)
    
    conn.close()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SkyHigh DTH Manager</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-100 p-8">
        <div class="max-w-4xl mx-auto bg-white shadow-lg rounded-lg overflow-hidden">
            <div class="bg-blue-600 p-4">
                <h1 class="text-white text-2xl font-bold">📡 SkyHigh DTH Management</h1>
                <p class="text-blue-100">DevOps Practice App v1.0</p>
            </div>
            
            <div class="p-6">
                <div class="mb-6 bg-blue-50 p-4 rounded border border-blue-200">
                    <h2 class="font-bold text-blue-800">Add New Subscription</h2>
                    <form action="/add" method="POST" class="mt-2 flex gap-2">
                        <input type="text" name="name" placeholder="Customer Name" required class="border p-2 rounded flex-grow">
                        <select name="package" class="border p-2 rounded">
                            <option value="Basic">Basic ($10)</option>
                            <option value="Sports">Sports ($20)</option>
                            <option value="Cinema">Cinema ($25)</option>
                            <option value="Mega">Mega Bundle ($40)</option>
                        </select>
                        <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">Add</button>
                    </form>
                </div>

                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-gray-200">
                            <th class="p-3 border-b">ID</th>
                            <th class="p-3 border-b">Name</th>
                            <th class="p-3 border-b">Package</th>
                            <th class="p-3 border-b">Status</th>
                            <th class="p-3 border-b">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for sub in subs %}
                        <tr class="hover:bg-gray-50">
                            <td class="p-3 border-b">{{ sub[0] }}</td>
                            <td class="p-3 border-b font-medium">{{ sub[1] }}</td>
                            <td class="p-3 border-b">
                                <span class="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded">{{ sub[2] }}</span>
                            </td>
                            <td class="p-3 border-b">
                                <span class="text-xs px-2 py-1 rounded {{ 'bg-green-100 text-green-800' if sub[3] == 'Active' else 'bg-red-100 text-red-800' }}">
                                    {{ sub[3] }}
                                </span>
                            </td>
                            <td class="p-3 border-b">
                                <a href="/delete/{{ sub[0] }}" class="text-red-600 hover:text-red-800 text-sm">Cancel</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            <div class="bg-gray-50 p-4 text-center text-gray-500 text-sm">
                DevOps Metrics available at <a href="/metrics" class="text-blue-500 underline">/metrics</a>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, subs=subs)

@app.route('/add', methods=['POST'])
def add_subscriber():
    name = request.form.get('name')
    pkg = request.form.get('package')
    conn = sqlite3.connect('dth.db')
    c = conn.cursor()
    c.execute("INSERT INTO subscribers (name, package, status) VALUES (?, ?, ?)", (name, pkg, 'Active'))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_subscriber(id):
    conn = sqlite3.connect('dth.db')
    c = conn.cursor()
    c.execute("UPDATE subscribers SET status = 'Cancelled' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/metrics')
def metrics():
    # This is the FIX: We explicitly set mimetype to text/plain
    return Response(generate_latest(), mimetype='text/plain')

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "version": "1.0.0"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
