from flask import jsonify
from flask_cors import CORS
from app import create_app

app = create_app()
CORS(app)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=3000,
        debug=True
    )
    
    