import sqlite3
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from git import Repo
import subprocess
import tempfile
import shutil

# Step 1: Set up SQLite database to store build history
def create_database():
    """Create the database and the 'builds' table if it doesn't exist."""
    conn = sqlite3.connect('build_history.db')  # Database file
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS builds (
            id INTEGER PRIMARY KEY,
            commit_id TEXT,
            build_date TEXT,
            build_logs TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Step 2: Log the build information
def log_build(commit_id, build_logs):
    """Log the build details to the database."""
    conn = sqlite3.connect('build_history.db')
    cursor = conn.cursor()
    build_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Current timestamp
    cursor.execute('''
        INSERT INTO builds (commit_id, build_date, build_logs)
        VALUES (?, ?, ?)
    ''', (commit_id, build_date, build_logs))
    conn.commit()
    conn.close()

# Step 3: Generate a unique URL for each build
def get_build_url(commit_id):
    """Generate a unique URL for a specific build."""
    return f"http://localhost:8008/build/{commit_id}"

# Step 4: Clone the repository and check out the branch
def clone_check(repo_url, branch):
    """Clone the repository and perform syntax checking."""
    temp_dir = tempfile.mkdtemp()
    try:
        repo = Repo.clone_from(repo_url, temp_dir, branch=branch)
        commit_id = repo.head.commit.hexsha  # Get commit ID
        return commit_id, temp_dir
    except Exception as e:
        return None, None
    finally:
        shutil.rmtree(temp_dir)

# Step 5: Run tests using pytest
def run_tests():
    """Run automated tests and return detailed success/failure output."""
    result = subprocess.run(["pytest", "--tb=short", "test/"], capture_output=True, text=True)
    return result.stdout if result.returncode != 0 else "Tests Passed"

# Step 6: Serve build information via an HTTP server
class BuildHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests for build details."""
        commit_id = self.path.split('/')[-1]  # Extract commit ID from URL
        
        # Fetch build details from the database
        conn = sqlite3.connect('build_history.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM builds WHERE commit_id = ?', (commit_id,))
        build = cursor.fetchone()
        conn.close()
        
        # Respond with the build information
        if build:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'commit_id': build[1],
                'build_date': build[2],
                'build_logs': build[3]
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'Build not found')

# Step 7: Run the HTTP server
def run_server():
    """Start the HTTP server to serve build information."""
    server = HTTPServer(('localhost', 8008), BuildHandler)
    print("Server running on port 8008...")
    server.serve_forever()

# Step 8: Handle the GitHub webhook and process builds
class SimpleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            payload = json.loads(post_data.decode('utf-8'))
            
            repo_url = payload['repository']['clone_url']
            branch = payload['ref'].split('/')[-1]  # Get the branch name
            
            # Clone the repository and get commit ID
            commit_id, temp_dir = clone_check(repo_url, branch)
            if not commit_id:
                raise Exception("Error cloning repository.")
            
            # Run tests
            test_results = run_tests()
            
            # Log build details
            log_build(commit_id, test_results)
            
            # Generate build URL
            build_url = get_build_url(commit_id)
            
            # Respond with success and build URL
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'status': 'success', 'build_url': build_url}
            self.wfile.write(json.dumps(response).encode())
        
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'status': 'error', 'message': str(e)}
            self.wfile.write(json.dumps(error_response).encode())

# Main Entry Point: Set up everything
def main():
    # Create the database if it doesn't exist
    create_database()
    
    # Run the HTTP server in a separate thread or process
    from threading import Thread
    thread = Thread(target=run_server)
    thread.daemon = True
    thread.start()

    # Start the webhook listener on port 8000
    server = HTTPServer(('localhost', 8000), SimpleHandler)
    print("Listening for webhooks on port 8000...")
    server.serve_forever()

# Run the script
if __name__ == "__main__":
    main()
