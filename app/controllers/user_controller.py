from flask import jsonify, request

from app.services.user_service import (
    create_user,
    get_user_by_id,
    
    update_user,
    deactivate_user,
    activate_user
)

def create_user_controller():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Falta llenar los campos del request"
        }), 400

    id_role = data.get("id_role")

    if id_role is None:
        return jsonify({
            "error": "El campo id_role es obligatorio"
        }), 400

    required_fields = [
        "document_type",
        "document_number",
        "first_names",
        "last_names",
        "email",
        "phone",
        "password",
    ]

    # Los campos son obligatorios para pacientes
    if id_role == 1:

        missing = [
            field
            for field in required_fields
            if not data.get(field)
        ]

        if missing:
            return jsonify({
                "error": (
                    "Faltan los campos requeridos: "
                    + ", ".join(missing)
                )
            }), 400

    try:
        user = create_user(
            id_role=id_role,
            document_type=data.get("document_type"),
            document_number=data.get("document_number"),
            first_names=data.get("first_names"),
            last_names=data.get("last_names"),
            email=data.get("email"),
            phone=data.get("phone"),
            password=data.get("password"),
        )

    except ValueError as e:
        return jsonify({
            "error": str(e)
        }), 409

    return jsonify(user_to_dict(user)), 201


def get_user_controller(user_id):
    user = get_user_by_id(user_id)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user_to_dict(user)), 200



def update_user_controller(user_id):
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    try:
        user = update_user(
            user_id=user_id,
            first_names=data.get("first_names"),
            last_names=data.get("last_names"),
            email=data.get("email"),
            phone=data.get("phone"),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    return jsonify(user_to_dict(user)), 200


def deactivate_user_controller(user_id):
    try:
        user = deactivate_user(user_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    return jsonify(user_to_dict(user)), 200

def activate_user_controller(user_id):
    try:
        user = activate_user(user_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    return jsonify(user_to_dict(user)), 200


def user_to_dict(user):
    #NO RETORNA EL PASSWORD hash
    return {
        "id": user.id,
        "document_type": user.document_type,
        "document_number": user.document_number,
        "first_names": user.first_names,
        "last_names": user.last_names,
        "email": user.email,
        "phone": user.phone,
        "is_active": user.is_active,
    }



