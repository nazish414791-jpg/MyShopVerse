"""
Entry Point

Run with:  python run.py
Or via CLI: flask run   (after setting FLASK_APP=run.py)
"""

import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from .env into the environment

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.shell_context_processor
def make_shell_context():
    """Enables `flask shell` to auto-import db and models for quick debugging."""
    return {"db": db}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
