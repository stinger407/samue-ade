from waitress import serve
from app import app

if __name__ == '__main__':
    print("=========================================")
    print("Starting Waitress production WSGI server...")
    print("Serving on http://127.0.0.1:8000")
    print("Press Ctrl+C to stop.")
    print("=========================================")
    serve(app, host='0.0.0.0', port=8000)
