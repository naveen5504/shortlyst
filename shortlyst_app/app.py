import os
from dotenv import load_dotenv
from flask import Flask
from applications.extensions import db, cors

# Load environment configuration
load_dotenv(override=True)

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    app.secret_key = os.getenv("SECRET_KEY", "shortlyst-secret-key-default")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI", "sqlite:///shortlyst.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB upload ceiling

    # Initialize extensions
    db.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})

    with app.app_context():
        # Ensure models are imported so db.create_all() registers all tables
        import models.models
        db.create_all()

    return app

app = create_app()

# Import controllers/routes
from controllers.controllers import *

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"Shortlyst running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
