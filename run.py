import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"\n==================================================")
    print(f"  AI Special Diet Planner Server Starting...")
    print(f"  Access locally: http://127.0.0.1:{port}")
    print(f"==================================================\n")
    app.run(host="127.0.0.1", port=port, debug=True)
