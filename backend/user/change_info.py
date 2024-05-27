from backend.models.basic_model import *
from app import *
from werkzeug.security import generate_password_hash, check_password_hash


# @app.route(f'{api}/update_photo/<user_id>', methods=['POST'])
# @jwt_required()
# def update_photo(user_id):
#     pprint(request.files)
#     photo = request.files['file']
#     user = User.query.filter(User.platform_id == user_id).first()
#     if photo and check_file(photo.filename):
#         get_img = add_file(photo,"image", app, File)
#         check_img_remove(user.file_id, File)
#         user.file_id = get_img
#         db.session.commit()
#         return edit_msg(f"Profil rasm", status=True, data=user.convert_json())
#     else:
#         return edit_msg(f"Profil rasm", status=False, data=user.convert_json())


@app.route(f'{api}/change_pas_user/<user_id>', methods=['POST'])
@jwt_required()
def change_pas_user(user_id):
    json = request.get_json()
    type = json['type']
    user = User.query.filter(User.id == user_id).first()
    if type == "info":
        User.query.filter(User.id == user_id).update({
            "username": json['username']
        })
        db.session.commit()
        return jsonify({
            "success": True,
            "msg": "User ma'lumoti o'zgartirildi o'zgartirildi",
            "data": user.convert_json()
        })
    else:
        password = json['password']
        hash = generate_password_hash(password, method='sha256')
        User.query.filter(User.id == user_id).update({'password': hash})
        db.session.commit()

        return jsonify({
            "success": True,
            "msg": "User paroli o'zgartirildi"
        })


@app.route(f'{api}/check_password', methods=['POST'])
@jwt_required()
def check_password():
    identity = get_jwt_identity()
    body = {}
    password = request.get_json()['password']
    username = User.query.filter_by(user_id=identity).first()
    if username and check_password_hash(username.password, password):
        body['password'] = True
    else:
        body['password'] = False

    return jsonify(body)
