#!/usr/bin/env python3
"""
🗺️ Staten Island Map Viewer Server
==================================

Serves the interactive map viewer with proper CORS headers
for loading local tile files.
"""

import http.server
import socketserver
import os
from urllib.parse import urlparse, parse_qs

class MapServerHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for tile loading
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Handle tile requests specifically
        if self.path.endswith('.png'):
            print(f"🖼️  Serving tile: {self.path}")
        
        super().do_GET()

def main():
    PORT = 8080
    
    # Change to the app directory to serve files
    os.chdir('/app')
    
    print("🗺️ STATEN ISLAND MAP VIEWER SERVER")
    print("=" * 50)
    print(f"🌐 Port: {PORT}")
    print(f"📂 Serving from: {os.getcwd()}")
    print(f"🔗 Map Viewer: http://localhost:{PORT}/staten_island_map_viewer.html")
    print()
    print("📁 Available files:")
    print(f"   • Interactive Map: /staten_island_map_viewer.html")
    print(f"   • Standard tiles: /game_tiles/tiles/")
    print(f"   • Topographic tiles: /game_tiles_topographic/tiles/")
    print()
    print("⚠️  Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        with socketserver.TCPServer(("", PORT), MapServerHandler) as httpd:
            print(f"✅ Server running at http://localhost:{PORT}/")
            print(f"🎯 Open: http://localhost:{PORT}/staten_island_map_viewer.html")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()