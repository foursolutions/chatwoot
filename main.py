# main.py

from dispatcher import app

# FastAPI will look for `app` here.
# No further code is needed, because `dispatcher.app` is a FastAPI() instance.

# If you want a simple “health check” endpoint, you can add it here:
@app.get("/health")
async def health_check():
    return {"status": "ok"}
