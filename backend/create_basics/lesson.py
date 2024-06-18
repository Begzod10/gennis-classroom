from backend.models.basic_model import Exercise, Lesson, LessonBlock, StudentLesson, Student, File, User, \
    StudentLessonArchive
from app import api, app, jsonify, request, db, or_, contains_eager
from backend.models.settings import iterate_models
from backend.basics.settings import add_file, check_img_remove, edit_msg, create_msg, del_msg
from pprint import pprint
from flask_jwt_extended import get_jwt_identity, jwt_required
import json
from sqlalchemy import desc as teskari


@app.route(f'{api}/filter_exercise/<subject_id>/<level_id>')
@jwt_required()
def filter_exercise(subject_id, level_id):
    exercises = Exercise.query.filter(Exercise.subject_id == subject_id, Exercise.level_id == level_id).order_by(
        Exercise.id).all()

    return jsonify({
        "data": iterate_models(exercises)
    })


@app.route(f'{api}/lessons/<int:level_id>', methods=["GET", 'POST'])
@jwt_required()
def lessons(level_id):
    identity = get_jwt_identity()
    user = User.query.filter_by(user_id=identity).first()

    if request.method == "POST":
        info = request.form.get("info")
        get_json = json.loads(info)

        selected_subject = get_json['subjectId']
        name = get_json['name']
        components = get_json['components']

        number_test = get_json['number_test']
        test_status = True if number_test else False
        chapter = get_json['chapter']
        order = 0
        lesson_get = Lesson.query.filter(Lesson.level_id == level_id, Lesson.subject_id == selected_subject,
                                         Lesson.chapter_id == chapter, Lesson.disabled == False).order_by(
            Lesson.order).all()
        if lesson_get:
            order = len(lesson_get)
        lesson_add = Lesson(subject_id=selected_subject, level_id=level_id, name=name, order=order, chapter_id=chapter,
                            test_status=test_status, test_numbers=number_test)
        lesson_add.add_commit()
        index_order = 0
        for component in components:
            exercise_id = None
            video_url = ''
            desc = component['text'] if 'text' in component else ''
            clone = ''
            if component['type'] == "exc":
                exercise_id = component['id']
                exercise = Exercise.query.filter(Exercise.id == exercise_id).first()

                lesson_add.exercises.append(exercise)
                db.session.commit()
            elif component['type'] == "video" or component['type'] == "snippet" or component['type'] == "file":
                video_url = ''
                if 'videoLink' in component:
                    video_url = component['videoLink']
                clone = component
            elif component['type'] == "text":
                clone = component['editorState']
            lesson_img = request.files.get(f'component-{component["index"]}-img')
            lesson_file = request.files.get(f'component-{component["index"]}-file')
            get_img = None
            if lesson_img:
                get_img = add_file(lesson_img, "img", app, File)

            if lesson_file:
                get_img = add_file(lesson_file, "file", app, File)
            lesson_block = LessonBlock(lesson_id=lesson_add.id, exercise_id=exercise_id, video_url=video_url, desc=desc,
                                       file_id=get_img, clone=clone, type_block=component['type'], order=index_order)
            lesson_block.add_commit()
            index_order += 1
        return create_msg(name, True)

    lessons = Lesson.query.filter(Lesson.level_id == level_id, Lesson.disabled != True).order_by(Lesson.order).all()
    if user.student:
        student = Student.query.filter(Student.user_id == user.id).first()
        for lesson in lessons:
            student_lesson = StudentLesson.query.filter(StudentLesson.lesson_id == lesson.id,
                                                        StudentLesson.student_id == student.id,
                                                        StudentLesson.level_id == level_id).first()
            if not student_lesson:
                student_lesson = StudentLesson(lesson_id=lesson.id, student_id=student.id, level_id=level_id)
                student_lesson.add_commit()

        student_lessons = db.session.query(StudentLesson).join(StudentLesson.lesson).options(
            contains_eager(StudentLesson.lesson)).filter(Lesson.disabled != True,
                                                         StudentLesson.student_id == student.id).order_by(
            StudentLesson.id).all()
        return jsonify({
            "length": len(lessons),
            "data": iterate_models(student_lessons)
        })

    return jsonify({
        "data": iterate_models(lessons),
        "length": len(lessons)
    })


@app.route(f'{api}/info_lesson/<chapter_id>/<order>', methods=['POST', 'GET', 'DELETE'])
@jwt_required()
def info_lesson(chapter_id, order):
    identity = get_jwt_identity()
    user = User.query.filter_by(user_id=identity).first()

    lesson = Lesson.query.filter(Lesson.chapter_id == chapter_id, Lesson.order == order,
                                 Lesson.disabled != True).first()

    lesson_id = lesson.id

    if request.method == "GET":
        next = Lesson.query.filter(Lesson.chapter_id == chapter_id, Lesson.order > lesson.order).filter(
            or_(Lesson.disabled == False, Lesson.disabled == None)).order_by(Lesson.order).first()

        prev = Lesson.query.filter(Lesson.chapter_id == chapter_id, Lesson.order < order).filter(
            or_(Lesson.disabled == False, Lesson.disabled == None)).order_by(teskari(Lesson.order)).first()
        next_order = False
        if next and next.order:
            next_order = next.order
        if prev and prev.order:
            prev_order = prev.order
        else:
            prev_order = 0
        lessons = Lesson.query.filter(Lesson.level_id == lesson.level_id, Lesson.disabled != True).order_by(
            Lesson.order).all()
        if user.student:
            student = Student.query.filter(Student.user_id == user.id).first()

            student_lesson = StudentLesson.query.filter(StudentLesson.lesson_id == lesson_id,
                                                        StudentLesson.student_id == student.id).first()
            student_lesson_archive = StudentLessonArchive.query.filter(
                StudentLessonArchive.student_lesson == student_lesson.id, StudentLessonArchive.student_id == student.id,
                StudentLessonArchive.status == False, StudentLessonArchive.lesson_id == lesson_id).first()

            return jsonify({
                "data": student_lesson.convert_json(entire=True,
                                                    student_lesson_archive_id=student_lesson_archive.id) if student_lesson_archive else lesson.convert_json(
                    entire=True),
                "length": len(lessons),
                'lesson_id': student_lesson.id,
                "next": next_order,
                "prev": prev_order,
                "archive_id": student_lesson_archive.id if student_lesson_archive else None
                # "student_exercises": iterate_models(student_exercises, entire=True)
            })
        return jsonify({
            "data": lesson.convert_json(entire=True),
            "length": len(lessons),
            "next": next_order,
            "prev": prev_order,

        })
    elif request.method == "POST":
        info = request.form.get("info")
        get_json = json.loads(info)

        name = get_json['name']
        chapter = get_json['chapter']

        lesson.name = name
        lesson.chapter_id = chapter
        number_test = get_json['number_test']
        test_status = True if number_test else False
        lesson.test_status = test_status
        lesson.test_numbers = number_test
        db.session.commit()
        components = get_json['components']
        index_order = 0

        for component in components:
            exercise_id = None
            video_url = ''
            clone = ''
            desc = component['text'] if 'text' in component else ''
            if component['type'] == "exc":
                exercise_id = component['id']
                exercise = Exercise.query.filter(Exercise.id == exercise_id).first()
                if exercise not in lesson.exercises:
                    lesson.exercises.append(exercise)
                    db.session.commit()
            elif component['type'] == "video":
                video_url = component['videoLink']
                clone = component
            elif component['type'] == "snippet" or component['type'] == "file":
                clone = component
            elif component['type'] == "text":
                clone = component['editorState']
            lesson_img = None
            lesson_file = None
            if "index" in component:
                lesson_img = request.files.get(f'component-{component["index"]}-img')
                lesson_file = request.files.get(f'component-{component["index"]}-file')
            get_img = None
            if lesson_img:
                get_img = add_file(lesson_img, "img", app, File)
                if 'block_id' in component:
                    lesson_block = LessonBlock.query.filter(LessonBlock.id == component['block_id']).first()
                    if lesson_block.file_id:
                        check_img_remove(lesson_block.file_id, File)
                        lesson_block.file_id = get_img
                        db.session.commit()
            if lesson_file:
                get_img = add_file(lesson_file, "file", app, File)
                if 'block_id' in component:
                    lesson_block = LessonBlock.query.filter(LessonBlock.id == component['block_id']).first()
                    if lesson_block.file_id:
                        check_img_remove(lesson_block.file_id, File)
                        lesson_block.file_id = get_img
                        db.session.commit()
            if 'block_id' in component:
                lesson_block = LessonBlock.query.filter(LessonBlock.id == component['block_id']).first()

                lesson_block.exercise_id = exercise_id
                lesson_block.video_url = video_url
                lesson_block.desc = desc
                lesson_block.clone = clone
                lesson_block.type_block = component['type']

                lesson_block.order = index_order
                db.session.commit()
            else:
                lesson_block = LessonBlock(lesson_id=lesson_id, exercise_id=exercise_id, video_url=video_url,
                                           desc=desc, order=index_order,
                                           file_id=get_img, clone=clone, type_block=component['type'])
                lesson_block.add_commit()
            index_order += 1
        return edit_msg(lesson.name, status=True)

    else:
        lesson.disabled = True
        db.session.commit()
        lessons = Lesson.query.filter(Lesson.id != lesson.id, Lesson.chapter_id == lesson.chapter_id,
                                      Lesson.level_id == lesson.level_id,
                                      Lesson.subject_id == lesson.subject_id, Lesson.disabled != True).order_by(
            Lesson.order).all()
        index = 0
        for less in lessons:
            less.order = index
            db.session.commit()
            index += 1
        return del_msg(lesson.name, True)


@app.route(f'{api}/del_lesson_block/<int:block_id>', methods=['DELETE'])
@jwt_required()
def del_lesson_block(block_id):
    lesson_block = LessonBlock.query.filter(LessonBlock.id == block_id).first()
    if lesson_block.file_id:
        check_img_remove(lesson_block.file_id, File)
    lesson_block.delete_commit()
    return del_msg(item="block", status=True)


@app.route(f'{api}/set_order', methods=['POST'])
@jwt_required()
def set_order():
    lessons_list = request.get_json()['lessons']
    lesson_get = Lesson.query.filter(Lesson.id == lessons_list[0]['id']).first()
    for lesson in lessons_list:
        Lesson.query.filter(Lesson.id == lesson['id']).update({"order": lesson['order']})
        db.session.commit()
    lessons = Lesson.query.filter(Lesson.level_id == lesson_get.level_id, Lesson.disabled != True).order_by(
        Lesson.order).all()
    return jsonify({
        "data": iterate_models(lessons),
        "length": len(lessons)
    })
