from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sqlite3
import tempfile
import shutil
from git import Repo
from runTests import run_tests
from datetime import datetime
from build_history import log_build, get_build_url, create_database
from clone import clone_check

# Step 1: Ensure the build history database exists
create_database()

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests for build details"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        message = "Hello World!"
        self.wfile.write(message.encode())

    def do_POST(self):
        """Handle POST requests for the webhook from GitHub"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data.decode('utf-8'))
            
            # Extracting repository URL and branch name from the payload
            repo_url = payload['repository']['clone_url']
            branch = payload['ref'].split('/')[-1]  # Get the branch name
            
            print(f"Received push event for branch: {branch} from repo: {repo_url}")

            # Step 2: Clone the repository and get commit ID
            commit_id, temp_dir = clone_check(repo_url, branch)
            if not commit_id:
                raise Exception("Error cloning repository.")
            
            # Step 3: Log only commit_id and build_date
            log_build(commit_id)  # Log the commit ID and build date
            
            # Step 4: Generate the build URL
            build_url = get_build_url(commit_id)

            # Respond with success and build URL
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'status': 'success', 'build_url': build_url}
            self.wfile.write(json.dumps(response).encode())
        
        except Exception as e:
            # If an error occurs, send a 500 error response
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'status': 'error', 'message': str(e)}
            self.wfile.write(json.dumps(error_response).encode())

def run_server(port):
    """Run the HTTP server"""
    server = HTTPServer(('', port), SimpleHandler)
    print(f'Server running on port {port}...')
    return server

