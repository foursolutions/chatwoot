# main.py
from dispatcher import app

@app.get("/health")
async def health_check():
    return {"status": "ok"}
