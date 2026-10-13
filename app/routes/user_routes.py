from flask import Blueprint
from app.controllers.user_controller import (
    create_user_controller,
    get_user_controller,
    update_user_controller,
    deactivate_user_controller,
    activate_user_controller
)
# from flask_jwt_extended import jwt_required
user_bp = Blueprint('user', __name__)


@user_bp.route('/user/generate', methods=['POST'])
#@jwt_required #guardar el token creando admin y luego agregando el jwt.
def create_user_route():
    return create_user_controller()


@user_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_route(user_id):
    return get_user_controller(user_id)


@user_bp.route('/user/<int:user_id>', methods=['PUT'])
def update_user_route(user_id):
    return update_user_controller(user_id)


@user_bp.route('/user/<int:user_id>/deactivate', methods=['PATCH'])
def deactivate_user_route(user_id):
    return deactivate_user_controller(user_id)

@user_bp.route('/user/<int:user_id>/activate', methods=['PATCH'])
def activate_user_route(user_id):
    return activate_user_controller(user_id)