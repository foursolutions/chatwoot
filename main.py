# begin main.py
import os
from dispatcher import app  # <- this loads all routes/handlers

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
# end main.py
