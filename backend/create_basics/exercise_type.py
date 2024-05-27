from app import api, app, request, jsonify, db
from backend.models.settings import iterate_models
from backend.models.basic_model import ExerciseTypes
from backend.basics.settings import create_msg, del_msg, edit_msg


@app.route(f'{api}/info_exercise_type', methods=['POST', 'GET'])
def info_exercise_type():
    if request.method == "POST":
        name = request.get_json()['name']
        type_exe = request.get_json()['type']

        try:
            add = ExerciseTypes(name=name, type_exercise=type_exe)
            add.add_commit()
            return create_msg(name, status=True, data=add.convert_json())
        except:
            return create_msg(name, status=False)
    else:
        exercise_types = ExerciseTypes.query.filter(ExerciseTypes.disabled == False).order_by(ExerciseTypes.id).all()

        return jsonify({
            "data": iterate_models(exercise_types, "exercise_types")
        })


@app.route(f'{api}/del_exercise_type/<int:type_id>', methods=['DELETE'])
def del_exercise_type(type_id):
    exercise_type = ExerciseTypes.query.filter(ExerciseTypes.id == type_id).first()
    try:
        exercise_type.disabled = True
        db.session.commit()
        return del_msg(exercise_type.name, True)
    except:
        return del_msg(exercise_type.name, False)


@app.route(f'{api}/edit_exercise_type/<int:type_id>', methods=['POST'])
def edit_exercise_type(type_id):
    name = request.get_json()['name']
    type_exe = request.get_json()['type']
    exercise_type = ExerciseTypes.query.filter(ExerciseTypes.id == type_id).first()
    try:

        exercise_type.name = name
        exercise_type.type_exercise = type_exe
        db.session.commit()
        return edit_msg(name, True, exercise_type.convert_json())
    except:
        return edit_msg(name, False, exercise_type.convert_json())
