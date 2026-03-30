import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for
import os

app = Flask(__name__)

DATABASE = 'bot_history.db'

def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def index():
    conn = get_db_connection()
    if conn is None:
        return "Error: Unable to connect to database."
    
    try
        scripts = conn.execute('SELECT * FROM history ORDER BY timestamp DESC').fetchall()
        
        # सांख्यिकी (Statistics)
        total_scripts = len(scripts)
        unique_users = len(set([s['user_id'] for s in scripts]))
        total_duration = sum([s['duration'] for s in scripts if s['duration'] is not None])

        conn.close()
        return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Video Script Bot Dashboard</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { background-color: #f8f9fa; padding: 20px; }
                .card { margin-bottom: 20px; border: none; box-shadow: 0 4px 8px rgba(0,0,0,0.1 ); }
                .card-header { background-color: #007bff; color: white; font-weight: bold; }
                .script-content { white-space: pre-wrap; background-color: #e9ecef; padding: 15px; border-radius: 5px; max-height: 200px; overflow-y: auto; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="mb-4 text-center">🎥 Video Script Bot Dashboard</h1>
                <div class="row mb-4 text-center">
                    <div class="col-md-4"><div class="card p-3"><h4>{{ total_scripts }}</h4><p>कुल स्क्रिप्ट्स</p></div></div>
                    <div class="col-md-4"><div class="card p-3"><h4>{{ unique_users }}</h4><p>यूनिक यूजर्स</p></div></div>
                    <div class="col-md-4"><div class="card p-3"><h4>{{ total_duration }} मिनट</h4><p>कुल अवधि</p></div></div>
                </div>
                <h2 class="mb-3">जनरेट की गई स्क्रिप्ट्स</h2>
                {% for script in scripts %}
                <div class="card">
                    <div class="card-header">ID: {{ script.id }} | यूजर: {{ script.username }}</div>
                    <div class="card-body">
                        <p><strong>विषय:</strong> {{ script.topic }} | <strong>अवधि:</strong> {{ script.duration }} मिनट</p>
                        <div class="script-content">{{ script.script }}</div>
                        <form action="{{ url_for('delete_script', script_id=script.id) }}" method="post" class="mt-2">
                            <button type="submit" class="btn btn-danger btn-sm">डिलीट करें</button>
                        </form>
                    </div>
                </div>
                {% endfor %}
            </div>
        </body>
        </html>
        ''', scripts=scripts, total_scripts=total_scripts, unique_users=unique_users, total_duration=total_duration)
    except Exception as e:
        return f"Error: {e}. Make sure the 'history' table exists."

@app.route('/delete/<int:script_id>', methods=['POST'])
def delete_script(script_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM history WHERE id = ?', (script_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT', 5000))
        
