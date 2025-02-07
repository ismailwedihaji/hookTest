from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import tempfile
import shutil
from git import Repo
from build_history import log_build, get_build_url, run_tests_and_log, create_database
from runTests import run_tests

# Create the database if it doesn't exist
create_database()

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        message = "Hello World!"
        self.wfile.write(message.encode())

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
            
            # Run tests and log build
            test_results = run_tests_and_log(commit_id)

            # Generate build URL
            build_url = get_build_url(commit_id)

            # Respond with success and build URL
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'status': 'success', 'build_url': build_url, 'test_results': test_results}
            self.wfile.write(json.dumps(response).encode())
        
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'status': 'error', 'message': str(e)}
            self.wfile.write(json.dumps(error_response).encode())

# Run the HTTP server
def run_server(port):
    server = HTTPServer(('', port), SimpleHandler)
    print(f'Server running on port {port}...')
    return server
