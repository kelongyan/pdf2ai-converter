#!/usr/bin/env python3
"""PDF2AI Converter Web UI 服务端"""

import sys
import webbrowser
import uvicorn

from api.app import create_app

app = create_app()

if __name__ == "__main__":
    port = 8000
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])

    dev = "--dev" in sys.argv

    if not dev:
        webbrowser.open(f"http://localhost:{port}")

    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=port,
        reload=dev,
    )
