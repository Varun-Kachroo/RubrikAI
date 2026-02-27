"""
api_simple.py - Simple API bridge for Student Portal
Connects student.html to SQLite database with scheduling support
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sqlite3
from urllib.parse import urlparse
from datetime import datetime
import sys
import errno
import os

# Railway injects $PORT automatically; fall back to 8502 for local dev
PORT = int(os.environ.get("PORT", 8502))

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rubriqai.db')


def init_db():
    """
    Create required tables if they don't exist.
    Runs on every startup — safe to call repeatedly.
    This ensures a fresh Railway deployment doesn't crash
    because the .db file wasn't in the repo.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS online_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            subject TEXT,
            duration_minutes INTEGER DEFAULT 60,
            questions TEXT NOT NULL,
            rubric TEXT,
            status TEXT DEFAULT 'active',
            starts_at TEXT,
            closes_at TEXT,
            total_submissions INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS online_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_code TEXT NOT NULL,
            student_name TEXT NOT NULL,
            student_email TEXT,
            answers TEXT NOT NULL,
            time_taken_minutes INTEGER,
            submitted_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialised")


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


class APIHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # ── Health check for Railway ──────────────────────────────────────
        if path == '/' or path == '/health':
            self._set_headers(200)
            self.wfile.write(json.dumps({
                'status': 'ok',
                'service': 'RubriqAI API'
            }).encode())
            return

        # ── Fetch test by code ────────────────────────────────────────────
        if path.startswith('/test/'):
            test_code = path.split('/')[-1]

            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT title, subject, duration_minutes, questions, status,
                           starts_at, closes_at
                    FROM online_tests
                    WHERE test_code = ?
                ''', (test_code,))

                row = cursor.fetchone()
                conn.close()

                if row:
                    status = row[4]
                    starts_at = row[5]
                    closes_at = row[6]
                    now = datetime.now().isoformat()

                    if starts_at and starts_at > now:
                        self._set_headers(403)
                        start_time = datetime.fromisoformat(starts_at).strftime('%Y-%m-%d %H:%M')
                        self.wfile.write(json.dumps({
                            'error': f'Test not started yet. Starts at {start_time}'
                        }).encode())
                        return

                    if closes_at and closes_at < now:
                        self._set_headers(403)
                        self.wfile.write(json.dumps({'error': 'Test has closed'}).encode())
                        return

                    if status not in ['active', 'scheduled']:
                        self._set_headers(403)
                        self.wfile.write(json.dumps({'error': f'Test is {status}'}).encode())
                        return

                    self._set_headers()
                    self.wfile.write(json.dumps({
                        'title': row[0],
                        'subject': row[1],
                        'duration': row[2],
                        'questions': json.loads(row[3])
                    }).encode())
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({'error': 'Test not found'}).encode())

            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({'error': str(e)}).encode())
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def do_POST(self):
        """Submit test answers"""
        if self.path == '/submit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO online_submissions
                    (test_code, student_name, student_email, answers, time_taken_minutes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    data['test_code'],
                    data['student_name'],
                    data.get('student_email', ''),
                    json.dumps(data['answers']),
                    data['time_taken']
                ))

                cursor.execute('''
                    UPDATE online_tests
                    SET total_submissions = total_submissions + 1
                    WHERE test_code = ?
                ''', (data['test_code'],))

                conn.commit()
                conn.close()

                self._set_headers()
                self.wfile.write(json.dumps({'success': True}).encode())

            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def run_server():
    # Always init DB tables first (safe on repeat calls)
    init_db()

    try:
        server = ReusableHTTPServer(('0.0.0.0', PORT), APIHandler)
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            print(f"❌ API server port {PORT} is already in use.")
            sys.exit(1)
        raise

    print(f'✅ API Server running on port {PORT}')
    print(f'📊 Students can now submit tests')
    print(f'⌨️  Press Ctrl+C to stop')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n👋 Shutting down API server...')
        server.shutdown()
        sys.exit(0)


if __name__ == '__main__':
    run_server()
