from flask import Flask, render_template_string, redirect, url_for, request
import sqlite3

app = Flask(__name__)
DB_PATH = "/home/ubuntu/bot_history.db"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Script Bot - Admin Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary-color: #0088cc;
            --secondary-color: #f4f7f6;
            --accent-color: #00d2ff;
            --danger-color: #dc3545;
        }
        body { 
            background-color: var(--secondary-color); 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .navbar {
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
            color: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .container { margin-top: 30px; }
        .card { 
            border: none;
            border-radius: 15px;
            margin-bottom: 25px; 
            box-shadow: 0 10px 20px rgba(0,0,0,0.05);
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .card-header {
            background-color: white;
            border-bottom: 1px solid #eee;
            border-radius: 15px 15px 0 0 !important;
            padding: 15px 20px;
        }
        .badge-custom {
            background-color: #e3f2fd;
            color: #007bff;
            border-radius: 20px;
            padding: 5px 15px;
            font-size: 0.85rem;
        }
        .script-container {
            background: #ffffff;
            border: 1px solid #e0e0e0;
            padding: 20px;
            border-radius: 10px;
            max-height: 300px;
            overflow-y: auto;
            font-size: 0.95rem;
            line-height: 1.6;
            color: #444;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary-color);
        }
        .stat-label {
            color: #777;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 0.8rem;
        }
        .btn-delete {
            color: var(--danger-color);
            border: 1px solid var(--danger-color);
            border-radius: 10px;
            padding: 5px 10px;
            font-size: 0.8rem;
            transition: all 0.3s;
        }
        .btn-delete:hover {
            background-color: var(--danger-color);
            color: white;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark py-3">
        <div class="container-fluid px-5">
            <span class="navbar-brand mb-0 h1">
                <i class="fab fa-telegram me-2"></i> Video Script Bot Admin
            </span>
            <div class="d-flex">
                <span class="text-white opacity-75">Live Monitoring Dashboard</span>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="stat-card">
                    <div class="stat-number">{{ total_scripts }}</div>
                    <div class="stat-label">Total Scripts Generated</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-card">
                    <div class="stat-number">{{ unique_users }}</div>
                    <div class="stat-label">Unique Users</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-card">
                    <div class="stat-number">{{ total_duration }}</div>
                    <div class="stat-label">Total Video Minutes</div>
                </div>
            </div>
        </div>

        <h3 class="mb-4 text-dark"><i class="fas fa-history me-2"></i> Recent Activity</h3>
        
        <div class="row">
            {% for row in history %}
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div>
                            <i class="fas fa-user-circle text-primary me-2"></i>
                            <strong>@{{ row[2] if row[2] else 'Unknown' }}</strong> 
                            <small class="text-muted ms-2">ID: {{ row[1] }}</small>
                        </div>
                        <div class="d-flex align-items-center">
                            <span class="badge-custom me-3"><i class="far fa-clock me-1"></i> {{ row[10] }}</span>
                            <form action="{{ url_for('delete_record', record_id=row[0]) }}" method="POST" onsubmit="return confirm('क्या आप वाकई इस रिकॉर्ड को डिलीट करना चाहते हैं?');">
                                <button type="submit" class="btn btn-delete">
                                    <i class="fas fa-trash-alt"></i> Delete
                                </button>
                            </form>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="row mb-3">
                            <div class="col-md-3">
                                <small class="text-muted d-block">Category</small>
                                <span class="fw-bold text-dark">{{ row[3] }}</span>
                            </div>
                            <div class="col-md-3">
                                <small class="text-muted d-block">Tone</small>
                                <span class="fw-bold text-dark">{{ row[4] }}</span>
                            </div>
                            <div class="col-md-3">
                                <small class="text-muted d-block">Audience</small>
                                <span class="fw-bold text-dark">{{ row[5] }}</span>
                            </div>
                            <div class="col-md-3">
                                <small class="text-muted d-block">Duration</small>
                                <span class="fw-bold text-dark">{{ row[7] }} Minutes</span>
                            </div>
                        </div>
                        <div class="mb-3">
                            <small class="text-muted d-block">Topic</small>
                            <p class="mb-0 fw-bold" style="color: #333;">{{ row[6] }}</p>
                        </div>
                        <div class="script-container">
                            {{ row[9] | replace('\n', '<br>') | safe }}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        {% if not history %}
        <div class="text-center py-5">
            <i class="fas fa-folder-open fa-4x text-muted mb-3"></i>
            <p class="text-muted">No data available yet. Start generating scripts on Telegram!</p>
        </div>
        {% endif %}
    </div>

    <footer class="text-center py-4 text-muted">
        <small>&copy; 2026 Video Script Bot Admin Panel</small>
    </footer>
</body>
</html>
'''

@app.route('/')
def index():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Fetch history
        cursor.execute('SELECT * FROM history ORDER BY timestamp DESC')
        history = cursor.fetchall()
        
        # Fetch stats
        cursor.execute('SELECT COUNT(*) FROM history')
        total_scripts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM history')
        unique_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(duration) FROM history')
        total_duration = cursor.fetchone()[0] or 0
        
        conn.close()
        return render_template_string(
            HTML_TEMPLATE, 
            history=history, 
            total_scripts=total_scripts, 
            unique_users=unique_users, 
            total_duration=round(total_duration, 1)
        )
    except Exception as e:
        return f"Error: {e}"

@app.route('/delete/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM history WHERE id = ?', (record_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error deleting record: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
