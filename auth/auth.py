from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from models import User
import bcrypt
from datetime import timedelta
from uuid import UUID

jwt = JWTManager()

def configure_auth(app):
    app.config["JWT_SECRET_KEY"] = "super-secret-key"  # Use env var in prod
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    jwt.init_app(app)

@jwt.user_identity_loader
def user_identity_lookup(user):
    return str(user.user_id)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.get(UUID(identity))