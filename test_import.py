import traceback

try:
    from app.asgi import app
    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")
    traceback.print_exc()