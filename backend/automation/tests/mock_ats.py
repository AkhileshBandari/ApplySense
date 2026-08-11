import os
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class MockATSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/success':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Application Submitted Successfully</h1></body></html>")
            return
            
        if self.path == '/captcha':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><iframe src='recaptcha_mock'></iframe></body></html>")
            return
            
        self.send_response(404)
        self.end_headers()

class MockATSServer:
    def __init__(self, port=8099):
        self.port = port
        self.server = HTTPServer(('localhost', port), MockATSHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        
    def start(self):
        self.thread.start()
        
    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
