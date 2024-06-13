from backend.models.basic_model import Student, StudentLesson, ExerciseAnswers, StudentExercise, StudentExerciseBlock, \
    User, StudentLevel, Exercise, ExerciseBlock, StudentChapter, StudentSubject, Lesson
from app import api, app, db, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.settings import iterate_models
from pprint import pprint
from .utils import update_student_datas, update_ratings


@app.route(f'{api}/finish/lesson/<int:lesson_id>')
@jwt_required()
def finish_lesson(lesson_id):
    identity = get_jwt_identity()
    user = User.query.filter_by(user_id=identity).first()
    student = Student.query.filter(Student.user_id == user.id).first()
    student_lesson = StudentLesson.query.filter(StudentLesson.id == lesson_id,
                                                StudentLesson.student_id == student.id).first()
    update_student_datas(student, student_lesson.lesson_id)
    return jsonify({
        "status": 'success'
    })


@app.route(f'{api}/complete_exercise', methods=['POST'])
@jwt_required()
def complete_exercise():
    identity = get_jwt_identity()
    user = User.query.filter_by(user_id=identity).first()
    answers = request.get_json()['block']
    lesson_id = request.get_json()['lessonId']
    exercise_id = request.get_json()['excId']
    student = Student.query.filter(Student.user_id == user.id).first()
    student_lesson = StudentLesson.query.filter(StudentLesson.lesson_id == lesson_id,
                                                StudentLesson.student_id == student.id).first()
    lesson = Lesson.query.filter(Lesson.id == lesson_id).first()
    pprint(request.get_json())
    for answer in answers:
        block = ExerciseBlock.query.filter(ExerciseBlock.id == answer['block_id']).first()
        exercise = Exercise.query.filter(Exercise.id == block.exercise_id).first()
        exist_block = StudentExerciseBlock.query.filter(StudentExerciseBlock.lesson_id == lesson_id,
                                                        StudentExerciseBlock.student_id == student.id,
                                                        StudentExerciseBlock.block_id == block.id,
                                                        StudentExerciseBlock.exercise_id == exercise.id,
                                                        StudentExerciseBlock.chapter_id == lesson.chapter_id).first()
        if not exist_block:
            student_exe_block = StudentExerciseBlock(student_id=student.id, block_id=block.id, exercise_id=exercise.id,
                                                     clone=answer['answers'], lesson_id=lesson_id,
                                                     chapter_id=lesson.chapter_id)
            student_exe_block.add_commit()

        if answer['innerType'] == "text" and answer['type'] == "question" or answer['innerType'] == "image" and answer[
            'type'] == "question" or answer['innerType'] == "imageInText" and answer['type'] == "question":
            exercise_answer = ExerciseAnswers.query.filter(ExerciseAnswers.block_id == answer['block_id'],
                                                           ExerciseAnswers.status == True).first()
            for ans in answer['answers']:
                if ans['checked'] == True:
                    status = False
                    if exercise_answer.order == ans['index']:
                        status = True
                    else:
                        exercise_answer = ExerciseAnswers.query.filter(ExerciseAnswers.block_id == answer['block_id'],
                                                                       ExerciseAnswers.order == ans['index']).first()
                    exist_exercise = StudentExercise.query.filter(StudentExercise.student_id == student.id,
                                                                  StudentExercise.lesson_id == lesson_id,
                                                                  StudentExercise.exercise_id == exercise.id,
                                                                  StudentExercise.answer_id == exercise_answer.id,
                                                                  StudentExercise.student_chapter_id == student_lesson.self_chapter_id,
                                                                  StudentExercise.chapter_id == lesson.chapter_id).first()
                    if not exist_exercise:
                        student_exercise = StudentExercise(student_id=student.id, lesson_id=lesson_id,
                                                           exercise_id=exercise.id, subject_id=exercise.subject_id,
                                                           type_id=exercise.type_id, level_id=exercise.level_id,
                                                           boolean=status, block_id=block.id,
                                                           answer_id=exercise_answer.id, value=ans['checked'],
                                                           student_chapter_id=student_lesson.self_chapter_id,
                                                           chapter_id=lesson.chapter_id)
                        student_exercise.add_commit()
                    else:
                        return jsonify({
                            'msg': 'seryoz'
                        })
            update_ratings(student, lesson_id)

        elif answer['type'] == "text":
            for ans in answer['answers']:
                if ans['type'] == "matchWord":
                    exercise_answer = ExerciseAnswers.query.filter(ExerciseAnswers.block_id == answer['block_id'],
                                                                   ExerciseAnswers.order == ans['index']).first()
                    if ans['index'] == ans['item']['index']:
                        exercise_status = True
                    else:
                        exercise_status = False
                    exist_exercise = StudentExercise.query.filter(StudentExercise.student_id == student.id,
                                                                  StudentExercise.lesson_id == lesson_id,
                                                                  StudentExercise.exercise_id == exercise.id,
                                                                  StudentExercise.answer_id == exercise_answer.id).first()
                    if not exist_exercise:
                        student_exercise = StudentExercise(student_id=student.id, lesson_id=lesson_id,
                                                           exercise_id=exercise.id, subject_id=exercise.subject_id,
                                                           type_id=exercise.type_id, level_id=exercise.level_id,
                                                           boolean=exercise_status, block_id=block.id,
                                                           answer_id=exercise_answer.id, value=ans['item'])
                        student_exercise.add_commit()
                    else:
                        return jsonify({
                            'msg': 'seryoz'
                        })
                else:
                    exercise_answer = ExerciseAnswers.query.filter(ExerciseAnswers.block_id == answer['block_id'],
                                                                   ExerciseAnswers.desc == ans['text']).first()
                    if ans['text'] == ans['value']:
                        exercise_status = True
                    else:
                        exercise_status = False

                    exist_exercise = StudentExercise.query.filter(StudentExercise.student_id == student.id,
                                                                  StudentExercise.lesson_id == lesson_id,
                                                                  StudentExercise.exercise_id == exercise.id,
                                                                  StudentExercise.answer_id == exercise_answer.id).first()
                    if not exist_exercise:
                        student_exercise = StudentExercise(student_id=student.id, lesson_id=lesson_id,
                                                           exercise_id=exercise.id, subject_id=exercise.subject_id,
                                                           type_id=exercise.type_id, level_id=exercise.level_id,
                                                           boolean=exercise_status, block_id=block.id,
                                                           answer_id=exercise_answer.id, value=ans['value'])
                        student_exercise.add_commit()
                    else:
                        return jsonify({
                            'msg': 'seryoz'
                        })
    update_student_datas(student, lesson_id)
    update_ratings(student, lesson_id)
    exercise_block = StudentExerciseBlock.query.filter(StudentExerciseBlock.lesson_id == lesson_id,
                                                       StudentExerciseBlock.student_id == student.id,
                                                       StudentExerciseBlock.exercise_id == exercise_id).order_by(
        StudentExerciseBlock.id).all()

    return jsonify({
        "success": True,
        "block": iterate_models(exercise_block)
    })
