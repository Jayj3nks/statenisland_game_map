#!/usr/bin/env python3
"""
🚀 Staten Island Map Viewer Server
Simple HTTP server to view your interactive map.
"""
import http.server
import socketserver
import os

PORT = 8080

os.chdir('/app')
print(f"🗺️ Staten Island Map Server")
print(f"🌐 Starting server on port {PORT}...")
print(f"🔗 Map Viewer: http://localhost:{PORT}/map_viewer.html")
print(f"⚠️  Press Ctrl+C to stop")

with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
    httpd.serve_forever()
