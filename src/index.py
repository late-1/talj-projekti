from os import getenv

from app import app

if __name__ == "__main__":
    app.run(
        host=getenv("HOST", "127.0.0.1"),
        port=int(getenv("PORT", "5001")),
        debug=getenv("DEBUG") == "true",
    )
