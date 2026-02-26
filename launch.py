#!/usr/bin/env python3
"""
RubriqAI Complete Platform Launcher
Starts: Student Portal (HTML) + API Bridge + Teacher Portal (Streamlit)
"""

import http.server
import socketserver
import webbrowser
import threading
import subprocess
import time
import os
import sys

PORT_STUDENT = 8000  # Student portal HTML
PORT_API = 8502      # API bridge for students
PORT_TEACHER = 8501  # Teacher Streamlit app

class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

def start_student_portal():
    """Start student HTML portal"""
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        with socketserver.TCPServer(("", PORT_STUDENT), QuietHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except:
        pass

def start_api():
    """Start API bridge"""
    time.sleep(1)
    try:
        subprocess.run(["python3", "api_simple.py"])
    except:
        print("⚠️  API server failed")

def start_teacher():
    """Start teacher Streamlit app"""
    time.sleep(2)
    try:
        subprocess.run(["streamlit", "run", "app.py", "--server.port", str(PORT_TEACHER), "--server.headless", "true"])
    except:
        print("❌ Streamlit not found")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 " + " "*20 + "RubriqAI Platform" + " "*20 + "🚀")
    print("="*70)
    
    print("\n📊 Starting all services...\n")
    
    # Start all services
    threading.Thread(target=start_student_portal, daemon=True).start()
    time.sleep(0.5)
    threading.Thread(target=start_api, daemon=True).start()
    time.sleep(1)
    
    print(f"✅ Student Portal:  http://localhost:{PORT_STUDENT}/student.html")
    print("✅ API Bridge:      http://localhost:{}".format(PORT_API))
    print("✅ Teacher Portal:  http://localhost:{}".format(PORT_TEACHER))
    
    print("\n" + "="*70)
    print("🎓 HOW IT WORKS:")
    print("  1. Teachers → http://localhost:{}".format(PORT_TEACHER))
    print("     - Create tests")
    print("     - Get test code")
    print("     - Download CSV")
    print()
    print("  2. Students → http://localhost:{}/student.html".format(PORT_STUDENT))
    print("     - Enter test code")
    print("     - Take test")
    print("     - Submit answers")
    print("="*70 + "\n")
    
    time.sleep(0.5)
    webbrowser.open(f"http://localhost:{PORT_TEACHER}")
    
    print("⌨️  Press Ctrl+C to stop all servers\n")
    
    try:
        start_teacher()
    except KeyboardInterrupt:
        print("\n" + "="*70)
        print("👋 Shutting down RubriqAI...")
        print("="*70 + "\n")
        sys.exit(0)
