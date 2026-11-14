from os import getenv

from app import app
from config import test_env

if __name__ == "__main__":
    app.run(
        host=getenv("HOST", "127.0.0.1"),
        port=int(getenv("PORT", "5001")),
        debug=not test_env,
    )
