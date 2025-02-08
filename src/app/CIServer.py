from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import shutil
from clone import clone_check
from runTests import run_tests

from notify import GithubNotification
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


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
            token = os.getenv('GITHUB_TOKEN')
            repo_url = payload['repository']['clone_url']
            
            print(payload['ref'].split('/')[-2].lower())
            if payload['ref'].split('/')[-2].lower() == 'issue':
                branch = payload['ref'].split('/')[-2] + '/' + payload['ref'].split('/')[-1]
            else:
                branch = payload['ref'].split('/')[-1]  # refs/heads/branch-name -> branch-name
            
            # Clone the repo and get the commit ID and temp_dir
            commit_id, temp_dir = clone_check(repo_url, branch)
            if not temp_dir:
                raise Exception("Error cloning repository.")
            
            # Run the tests using temp_dir
            test_results = run_tests(temp_dir)

            # Initialize GithubNotification after successful execution
            gh = GithubNotification(payload['organization']['login'], payload['repository']['name'], token, "http://localhost:8008", "ci/tests")
            gh.send_commit_status("success", "Tests passed", payload['after'], "1") 

            if test_results:
                print("Tests Passed")
            else:
                print("One or more tests Failed")
                
            # Clean up the temp folder after use
            remove_temp_folder(temp_dir)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'status': 'success', 'message': "Repository cloned and tests run successfully", "test_results": test_results}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"Error: {str(e)}")
            # Ensure gh is initialized before calling it
            if 'gh' in locals():
                gh.send_commit_status("failure", "Tests failed", payload['after'], "1")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'status': 'error', 'message': str(e)}
            self.wfile.write(json.dumps(error_response).encode())

def remove_temp_folder(folder):
    shutil.rmtree(folder, onerror=handle_remove_readonly)

def handle_remove_readonly(func, path, exc):
    # Change permissions to writeable if needed
    excvalue = exc[1]
    if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == errno.EACCES:
        # Ensure the item is writeable
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        func(path)  # Retry the removal
    else:
        raise excvalue

def run_server(port):
    server = HTTPServer(('', port), SimpleHandler)
    print(f'Server running on port {port}...')
    return server
