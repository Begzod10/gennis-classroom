from backend.models.basic_model import ExerciseTypes, SubjectLevel, Subject, Exercise, File, ExerciseAnswers, \
    StudentExercise, ExerciseBlock, ExerciseBlockImages, Component
from app import request, app, api, db, jsonify
from backend.models.settings import iterate_models, delete_list_models
from backend.basics.settings import check_img_remove, del_msg, edit_msg, create_msg, add_file
import json
from pprint import pprint
from flask_jwt_extended import jwt_required


@app.route(f'{api}/info_exercise', methods=['POST', 'GET'])
@jwt_required()
def info_exercise():
    if request.method == "POST":
        info = request.form.get("info")
        get_json = json.loads(info)
        selected_level = get_json['selectedLevel']
        selected_subject = get_json['selectedSubject']
        name = get_json['title']
        exercise_type = get_json['typeEx']
        components = get_json['components']
        get_exercise_type = ExerciseTypes.query.filter(ExerciseTypes.id == exercise_type).first()
        get_level = SubjectLevel.query.filter(SubjectLevel.id == selected_level).first()
        get_subject = Subject.query.filter(Subject.id == selected_subject).first()
        random_status = False

        if 'random' in get_json:
            random_status = get_json['random']
        exist = Exercise.query.filter(Exercise.name == name).first()
        if not exist:
            add_exercise = Exercise(name=name, level_id=get_level.id, random_status=random_status,
                                    type_id=get_exercise_type.id,
                                    subject_id=get_subject.id)
            add_exercise.add_commit()

            for component in components:
                type_component = component['type']
                text = ''
                if 'text' in component:
                    text = component['text']
                get_component = Component.query.filter(Component.name == type_component).first()
                if not get_component:
                    get_component = Component(name=type_component)
                    get_component.add_commit()

                audio_url = None
                if type_component == "audio":
                    audio = request.files.get(f'component-{component["index"]}-audio')
                    audio_url = add_file(audio, type_file="audio", app=app, File=File)

                word_img = request.files.get(f'component-{component["index"]}-img')
                get_img = None
                if word_img:
                    get_img = add_file(word_img, type_file="img", app=app, File=File)
                inner_type = ''
                if 'innerType' in component:
                    inner_type = component['innerType']
                clone = ''
                if 'clone' in component:
                    clone = component['clone']
                if 'editorState' in component:
                    clone = component['editorState']
                if type_component == "question":
                    clone = component
                add_exe = ExerciseBlock(desc=text, exercise_id=add_exercise.id, component_id=get_component.id,
                                        clone=clone, img_info=get_img, audio_info=audio_url,
                                        inner_type=inner_type)
                add_exe.add_commit()
                if type_component == "text":
                    if "words" in component:
                        add_exe.for_words = component['words']
                        db.session.commit()
                        for word in component['words']:
                            exercise_answer = ExerciseAnswers(
                                exercise_id=add_exercise.id,
                                block_id=add_exe.id,
                                desc=word['text'], order=word['index'])
                            db.session.add(exercise_answer)
                            db.session.commit()
                if type_component == "question" and inner_type == "imageInText":

                    for word in component['words']:

                        if 'active' in word:
                            get_img = None
                            type_img = ''
                            word_img = request.files.get(f'component-{component["index"]}-words-index-{word["id"]}')
                            if word_img:
                                get_img = add_file(word_img, type_file="img", app=app, File=File)
                                block_img = ExerciseBlockImages(file_id=get_img, block_id=add_exe.id, order=word['id'],
                                                                type_image="word")
                                block_img.add_commit()
                            else:
                                answer_exercise = ExerciseAnswers(exercise_id=add_exercise.id,
                                                                  subject_id=get_subject.id,
                                                                  level_id=get_level.id, desc=word['word'],
                                                                  file_id=get_img,
                                                                  type_id=get_exercise_type.id, order=word['id'],
                                                                  block_id=add_exe.id,
                                                                  status=word['active'], type_img=type_img)
                                answer_exercise.add_commit()
                        if 'type' in word:
                            answer_exercise = ExerciseAnswers(exercise_id=add_exercise.id, subject_id=get_subject.id,
                                                              level_id=get_level.id, desc=word['text'],
                                                              type_id=get_exercise_type.id, order=word['index'],
                                                              block_id=add_exe.id)
                            answer_exercise.add_commit()

                if 'variants' in component:

                    type_img = ''
                    if component['variants']['type'] == "select":
                        for option in component['variants']['options']:
                            if option['innerType'] == "text":
                                get_img = None
                                type_img = ''
                            else:

                                word_img = request.files.get(
                                    f'component-{component["index"]}-variants-index-{option["index"]}')
                                get_img = add_file(word_img, type_file="img", app=app, File=File)
                                type_img = 'variant_img'

                            answer_exercise = ExerciseAnswers(exercise_id=add_exercise.id, subject_id=get_subject.id,
                                                              level_id=get_level.id, desc=option['text'],
                                                              file_id=get_img, status=option['isTrue'],
                                                              type_id=get_exercise_type.id, order=option['index'],
                                                              type_img=type_img, block_id=add_exe.id)

                            answer_exercise.add_commit()
                    else:
                        answer_exercise = ExerciseAnswers(exercise_id=add_exercise.id, subject_id=get_subject.id,
                                                          level_id=get_level.id, desc=component['variants']['answer'],
                                                          type_img=type_img,
                                                          type_id=get_exercise_type.id, status=True,
                                                          block_id=add_exe.id)

                        answer_exercise.add_commit()
            return create_msg(name, True)

        else:
            return jsonify({
                "msg": f"Bu {name} nomdagi mashq yaratilgan"
            })
    exercises = Exercise.query.order_by(Exercise.id).all()
    return jsonify({
        "data": iterate_models(exercises, entire=True)
    })


@app.route(f'{api}/exercise_profile/<int:exercise_id>', methods=['POST', 'GET', 'DELETE'])
@jwt_required()
def exercise_profile(exercise_id):
    if request.method == "GET":
        exercise = Exercise.query.filter(Exercise.id == exercise_id).first()

        return jsonify({
            "data": exercise.convert_json(entire=True)
        })
    elif request.method == "DELETE":
        exercise = Exercise.query.filter(Exercise.id == exercise_id).first()
        name = exercise.name
        blocks = ExerciseBlock.query.filter(ExerciseBlock.exercise_id == exercise_id).all()
        for block in blocks:
            block_img = ExerciseBlockImages.query.filter(ExerciseBlockImages.block_id == block.id).all()
            for img in block_img:
                check_img_remove(img.img_id, File=File)
                img.delete_commit()
        exercise_answers = ExerciseAnswers.query.filter(ExerciseAnswers.exercise_id == exercise_id).all()
        donelessons = StudentExercise.query.filter(StudentExercise.exercise_id == exercise_id).all()
        # try:
        delete_list_models(blocks, File, type="double")
        delete_list_models(exercise_answers, File)
        delete_list_models(donelessons, File)
        exercise.delete_commit()
        return del_msg(item=name, status=True)
        # except:
        #     return del_msg(item=name, status=False)
    elif request.method == "POST":
        info = request.form.get("info")
        get_json = json.loads(info)
        selected_level = get_json['selectedLevel']
        selected_subject = get_json['selectedSubject']
        name = get_json['title']
        exercise_type = get_json['typeEx']
        components = get_json['components']
        random_status = False
        if 'random' in get_json:
            random_status = get_json['random']
        get_exercise_type = ExerciseTypes.query.filter(ExerciseTypes.id == exercise_type).first()
        get_level = SubjectLevel.query.filter(SubjectLevel.id == selected_level).first()
        get_subject = Subject.query.filter(Subject.id == selected_subject).first()
        Exercise.query.filter(Exercise.id == exercise_id).update({
            "subject_id": get_subject.id,
            "type_id": get_exercise_type.id,
            "level_id": get_level.id,
            "name": name,
            "random_status": random_status
        })
        db.session.commit()
        exercise = Exercise.query.filter(Exercise.id == exercise_id).first()
        order = 0

        for component in components:

            type_component = component['type']
            get_component = Component.query.filter(Component.name == type_component).first()
            if not get_component:
                get_component = Component(name=type_component)
                get_component.add_commit()
            text = ''
            if 'text' in component:
                text = component['text']
            audio_url = None
            if type_component == "audio":
                audio = request.files.get(f'component-{component["index"]}-audio')
                if audio:
                    audio_url = add_file(audio, "audio", app, File)

            word_img = request.files.get(f'component-{component["index"]}-img')
            get_file = None
            if word_img:
                get_file = add_file(word_img, type_file="img", app=app, File=File)
            pprint(audio_url)
            inner_type = ''
            clone = component
            if 'editorState' in component:
                clone = component['editorState']
            if 'clone' in component:
                clone = component['clone']
            if type_component == "question":
                clone = component
            if 'innerType' in component:
                inner_type = component['innerType']
            if 'block_id' not in component:
                print(True)
                block = ExerciseBlock(desc=text, exercise_id=exercise.id, component_id=get_component.id,
                                      clone=clone, img_info=get_file, audio_info=audio_url,
                                      inner_type=inner_type, order=order)
                block.add_commit()
                audio_url = None
                if type_component == "text":
                    if "words" in component:
                        block.for_words = component['words']
                        db.session.commit()
                        for word in component['words']:
                            exercise_answer = ExerciseAnswers(
                                exercise_id=exercise.id,
                                block_id=block.id,
                                desc=word['text'], order=word['index'])
                            db.session.add(exercise_answer)
                            db.session.commit()
                if type_component == "question" and inner_type == "imageInText":

                    for word in component['words']:

                        if 'active' in word:
                            get_img = None
                            type_img = ''
                            word_img = request.files.get(f'component-{component["index"]}-words-index-{word["id"]}')
                            if word_img:
                                get_img = add_file(word_img, type_file="img", app=app, File=File)
                                block_img = ExerciseBlockImages(file_id=get_img, block_id=block.id, order=word['id'],
                                                                type_image="word")
                                block_img.add_commit()
                            else:
                                answer_exercise = ExerciseAnswers(exercise_id=exercise.id,
                                                                  subject_id=get_subject.id,
                                                                  level_id=get_level.id, desc=word['word'],
                                                                  file_id=get_img,
                                                                  type_id=get_exercise_type.id, order=word['id'],
                                                                  block_id=block.id,
                                                                  status=word['active'], type_img=type_img)
                                answer_exercise.add_commit()
                        if 'type' in word:
                            answer_exercise = ExerciseAnswers(exercise_id=exercise.id, subject_id=get_subject.id,
                                                              level_id=get_level.id, desc=word['text'],
                                                              type_id=get_exercise_type.id, order=word['index'],
                                                              block_id=block.id)
                            answer_exercise.add_commit()
                if 'variants' in component:
                    if component['variants']['type'] == "select":
                        for option in component['variants']['options']:
                            if option['innerType'] == "text":
                                get_file = None
                                type_img = ''
                            else:
                                word_img = request.files.get(
                                    f'component-{component["index"]}-variants-index-{option["index"]}')
                                if word_img:
                                    get_file = add_file(word_img, type_file="img", app=app, File=File)
                                type_img = 'variant_img'
                            answer_exercise = ExerciseAnswers(exercise_id=exercise.id, subject_id=get_subject.id,
                                                              level_id=get_level.id, desc=option['text'],
                                                              file_id=get_file, status=option['isTrue'],
                                                              type_id=get_exercise_type.id, order=option['index'],
                                                              type_img=type_img, block_id=block.id)

                            answer_exercise.add_commit()
                    else:
                        type_img = ''
                        answer_exercise = ExerciseAnswers(exercise_id=exercise.id, subject_id=get_subject.id,
                                                          level_id=get_level.id, desc=component['variants']['answer'],
                                                          type_img=type_img, order=0,
                                                          type_id=get_exercise_type.id, status=True, block_id=block.id)

                        answer_exercise.add_commit()
            else:
                if 'clone' in component:
                    clone = component['clone']
                if 'editorState' in component:
                    clone = component['editorState']
                if type_component == "question":
                    clone = component

                block = ExerciseBlock.query.filter(ExerciseBlock.id == component['block_id']).first()
                if not audio_url:
                    if block.audio:
                        audio_url = block.audio.id
                else:
                    if block.audio:
                        check_img_remove(block.audio.id, File=File)
                if not get_file:
                    get_file = block.img_info
                else:
                    if block.img_info:
                        check_img_remove(block.img_info, File=File)
                block.desc = text
                block.order = order
                block.audio_info = audio_url
                block.img_info = get_file
                block.component_id = get_component.id
                block.inner_type = component['innerType'] if 'innerType' in component else None
                block.clone = clone
                block.for_words = component['words'] if 'words' in component else None
                db.session.commit()

                if 'words' in component:
                    for word in component['words']:
                        if 'active' in word and word['active'] == True and inner_type == "image":
                            exercise_answer = ExerciseAnswers.query.filter(
                                ExerciseAnswers.block_id == component['block_id'],
                                ExerciseAnswers.order == word['id']).first()

                            word_img = request.files.get(f'component-{component["index"]}-words-index-{word["id"]}')
                            block_img = ExerciseBlockImages.query.filter(
                                ExerciseBlockImages.block_id == block.id).first()
                            type_img = "question_img"
                            if word_img:
                                get_file = add_file(word_img, type_file="img", app=app, File=File)
                            else:
                                if block_img:
                                    type_img = block_img.type_image
                                    get_file = block_img.file_id

                            if block_img:
                                block_img.file_id = get_file
                                block_img.type_image = type_img
                            if exercise_answer:
                                exercise_answer.desc = word['word']
                                exercise_answer.status = word['active']
                                exercise_answer.subject_id = get_subject.id
                                exercise_answer.order = word['id']
                                exercise_answer.block_id = block.id
                                exercise_answer.type_id = get_exercise_type.id
                                exercise_answer.level_id = get_level.id
                                exercise_answer.exercise_id = exercise.id
                            db.session.commit()
                if type_component == "question" and inner_type == "imageInText":
                    for word in component['words']:

                        if 'active' in word:
                            type_img = 'word'
                            word_img = request.files.get(
                                f'component-{component["index"]}-words-index-{word["id"]}')
                            if word_img:
                                get_img = add_file(word_img, type_file="img", app=app, File=File)
                                block_img = ExerciseBlockImages.query.filter(
                                    ExerciseBlockImages.block_id == block.id,
                                    ExerciseBlockImages.order == word['id']).first()
                                if block_img:
                                    block_img.file_id = get_img
                                    block_img.type_image = type_img
                                else:
                                    block_img = ExerciseBlockImages(file_id=get_img, block_id=block.id,
                                                                    order=word['id'],
                                                                    type_image="word")
                                    block_img.add_commit()
                if 'variants' in component:

                    if component['variants']['type'] == "select":

                        for option in component['variants']['options']:
                            exercise_answer = ExerciseAnswers.query.filter(
                                ExerciseAnswers.block_id == component['block_id'],
                                ExerciseAnswers.order == option['index']).first()
                            if option['innerType'] == "text":
                                get_file = None
                                type_img = ''

                            else:
                                word_img = request.files.get(
                                    f'component-{component["index"]}-variants-index-{option["index"]}')

                                if word_img:
                                    get_file = add_file(word_img, type_file="img", app=app, File=File)
                                else:
                                    get_file = exercise_answer.file_id
                                type_img = 'variant_img'
                            if exercise_answer:
                                exercise_answer.file_id = get_file
                                exercise_answer.type_img = type_img
                                exercise_answer.subject_id = get_subject.id
                                exercise_answer.order = option['index']
                                exercise_answer.block_id = block.id
                                exercise_answer.type_id = get_exercise_type.id
                                exercise_answer.level_id = get_level.id
                                exercise_answer.exercise_id = exercise.id
                                exercise_answer.desc = option['text']
                                exercise_answer.status = option['isTrue']
                                db.session.commit()
                            else:
                                exercise_answer = ExerciseAnswers(block_id=component['block_id'],
                                                                  order=option['index'])
                                exercise_answer.add_commit()
                                exercise_answer.file_id = get_file
                                exercise_answer.type_img = type_img
                                exercise_answer.subject_id = get_subject.id
                                exercise_answer.order = option['index']
                                exercise_answer.block_id = block.id
                                exercise_answer.type_id = get_exercise_type.id
                                exercise_answer.level_id = get_level.id
                                exercise_answer.exercise_id = exercise.id
                                exercise_answer.desc = option['text']
                                exercise_answer.status = option['isTrue']
                                db.session.commit()
                if 'type' in component:
                    if component['type'] == "text":

                        exercise_answer = ExerciseAnswers.query.filter(ExerciseAnswers.exercise_id == exercise_id,
                                                                       ExerciseAnswers.block_id == component[
                                                                           'block_id']).all()
                        for ans in exercise_answer:
                            db.session.delete(ans)
                            db.session.commit()
                        if 'words' in component:
                            for word in component['words']:
                                answer_exercise = ExerciseAnswers(exercise_id=exercise_id, subject_id=get_subject.id,
                                                                  level_id=get_level.id, desc=word['text'],
                                                                  type_id=get_exercise_type.id, order=word['index'],
                                                                  block_id=block.id)
                                answer_exercise.add_commit()
            order += 1
        return edit_msg(exercise.name, status=True, data=exercise.convert_json(entire=True))


@app.route(f'{api}/delete_block/<int:block_id>', methods=['DELETE'])
@jwt_required()
def delete_block(block_id):
    block = ExerciseBlock.query.filter(ExerciseBlock.id == block_id).first()
    exercise_answers = ExerciseAnswers.query.filter(ExerciseAnswers.block_id == block_id).all()
    delete_list_models(exercise_answers, File)
    if block.audio_info:
        check_img_remove(block.audio_info, File=File)
    if block.img_info:
        check_img_remove(block.img_info, File=File)
    block_img = ExerciseBlockImages.query.filter(ExerciseBlockImages.block_id == block_id).all()
    for img in block_img:
        check_img_remove(img.file_id, File=File)
        img.delete_commit()
    block.delete_commit()

    return del_msg(item="block", status=True)
