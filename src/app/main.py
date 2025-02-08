from CIServer import SimpleHandler
from http.server import HTTPServer, BaseHTTPRequestHandler
from CIServer import run_server


server = run_server(8009)
server.serve_forever()


