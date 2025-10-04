#!/usr/bin/env python3
"""
🚀 Staten Island Map Preview Server
==================================

Starts a local web server to preview your unified Staten Island map
before Unity development.

Usage:
    python3 start_preview.py

Then open: http://localhost:8080/unified_map_preview.html
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

def main():
    # Change to the app directory
    os.chdir('/app')
    
    PORT = 8080
    
    print("🗺️ STATEN ISLAND MAP PREVIEW SERVER")
    print("=" * 50)
    print(f"🌐 Starting server on port {PORT}...")
    print(f"📂 Serving from: {os.getcwd()}")
    print(f"🔗 Preview URL: http://localhost:{PORT}/unified_map_preview.html")
    print("\n📋 Available Files:")
    print(f"   • Unified Map Preview: http://localhost:{PORT}/unified_map_preview.html")
    print(f"   • Original Map Viewer: http://localhost:{PORT}/game_tiles/map_viewer.html")
    print(f"   • Topographic Viewer: http://localhost:{PORT}/game_tiles_topographic/topographic_viewer.html")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
            print(f"✅ Server running at http://localhost:{PORT}/")
            print(f"🎯 Open this URL to view your map: http://localhost:{PORT}/unified_map_preview.html")
            
            # Try to open browser automatically (may not work in all environments)
            try:
                webbrowser.open(f"http://localhost:{PORT}/unified_map_preview.html")
                print("🌐 Attempting to open browser automatically...")
            except:
                print("📝 Please manually open the URL above in your browser")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print(f"💡 Try a different port or check if {PORT} is already in use")

if __name__ == "__main__":
    main()