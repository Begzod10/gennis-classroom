from app import app, api, db, request, jsonify, platform_server
from flask_jwt_extended import get_jwt_identity, jwt_required
from backend.models.basic_model import User, SubjectLevel, StudentLevel, Student
from backend.basics.settings import create_msg, edit_msg, del_msg
from backend.models.settings import iterate_models, send_subject_server


@app.route(f'{api}/info_level/<int:subject_id>', methods=['POST', 'GET'])
@jwt_required()
def info_level(subject_id):
    identity = get_jwt_identity()
    user = User.query.filter_by(user_id=identity).first()
    # if user.student:
    # subject_levels = SubjectLevel.query.filter(SubjectLevel.subject_id == subject_id,
    #                                            SubjectLevel.disabled == False,
    #                                            SubjectLevel.lesson != None).order_by(SubjectLevel.id).all()
    # else:
    subject_levels = SubjectLevel.query.filter(SubjectLevel.subject_id == subject_id,
                                               SubjectLevel.disabled == False).order_by(SubjectLevel.id).all()
    server_levels = SubjectLevel.query.order_by(
        SubjectLevel.id).all()
    send_subject_server("levels", platform_server, server_levels)
    if user.student:
        student = Student.query.filter(Student.user_id == user.id).first()
        student_level = StudentLevel.query.filter(StudentLevel.subject_id == subject_id,
                                                  StudentLevel.student_id == student.id).join(SubjectLevel).order_by(
            SubjectLevel.id).all()
        print(student_level)
        return jsonify({
            "data": iterate_models(student_level)
        })

    if request.method == "POST":
        get_json = request.get_json()
        name = get_json['name']
        desc = get_json['desc']
        try:
            add = SubjectLevel(name=name, desc=desc, subject_id=subject_id)
            add.add_commit()
            subject_levels = SubjectLevel.query.filter(SubjectLevel.subject_id == subject_id,
                                                       SubjectLevel.disabled == False).order_by(
                SubjectLevel.id).all()
            server_levels = SubjectLevel.query.order_by(
                SubjectLevel.id).all()
            send_subject_server("levels", platform_server, server_levels)
            return create_msg(f"{name}", status=True, data=iterate_models(subject_levels))

        except:
            return create_msg(f"{name}", status=False, data=iterate_models(subject_levels))

    else:
        return jsonify({
            "data": iterate_models(subject_levels)
        })


@app.route(f'{api}/deleted_levels/<int:subject_id>')
@jwt_required()
def deleted_levels(subject_id):
    subject_levels = SubjectLevel.query.filter(SubjectLevel.subject_id == subject_id,
                                               SubjectLevel.disabled == True).order_by(SubjectLevel.id).all()
    return jsonify({
        "data": iterate_models(subject_levels)
    })


@app.route(f'{api}/level/<int:level_id>')
@jwt_required()
def level(level_id):
    level_get = SubjectLevel.query.filter(SubjectLevel.id == level_id).first()
    return jsonify({
        "data": level_get.convert_json()
    })


@app.route(f'{api}/edit_level/<int:level_id>', methods=['POST', 'DELETE'])
@jwt_required()
def edit_level(level_id):
    if request.method == "POST":
        get_json = request.get_json()
        name = get_json['name']
        desc = get_json['desc']
        level = SubjectLevel.query.filter(SubjectLevel.id == level_id).first()
        try:
            SubjectLevel.query.filter(SubjectLevel.id == level_id).update({
                "name": name,
                "desc": desc
            })
            db.session.commit()
            server_levels = SubjectLevel.query.order_by(
                SubjectLevel.id).all()
            send_subject_server("levels", platform_server, server_levels)
            return edit_msg(f"{name}", status=True, data=level.convert_json())
        except:
            return edit_msg(f"{name}", status=False, data=level.convert_json())
    else:
        level_name = SubjectLevel.query.filter(SubjectLevel.id == level_id).first()
        name = level_name.name
        if level_name.disabled:
            level_name.disabled = False
            db.session.commit()
            server_levels = SubjectLevel.query.order_by(
                SubjectLevel.id).all()
            send_subject_server("levels", platform_server, server_levels)
            return edit_msg(f"{name}", status=True)
        else:
            level_name.disabled = True
            db.session.commit()
            server_levels = SubjectLevel.query.order_by(
                SubjectLevel.id).all()
            send_subject_server("levels", platform_server, server_levels)
            return del_msg(item=name, status=True)
