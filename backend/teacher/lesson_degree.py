from app import app, api, jsonify, request, contains_eager, db
from backend.models.basic_model import Exercise, Subject, SubjectLevel, StudentExercise, StudentLevel, StudentLesson, \
    ExerciseBlock, Group, Student, Teacher, Chapter, Lesson, StudentChapter, ExerciseAnswers, StudentExerciseBlock, \
    StudentLessonArchive
from backend.models.settings import iterate_models
from flask_jwt_extended import jwt_required
from sqlalchemy.orm import joinedload


@app.route(f'{api}/group_degree', methods=['POST'])
@jwt_required()
def group_degree():
    group_id = request.get_json()['group_id']
    level_id = request.get_json()['level_id']
    chapter_id = request.get_json()['chapter_id'] if 'chapter_id' in request.get_json() else None
    lesson_id = request.get_json()['lesson_id'] if 'lesson_id' in request.get_json() else None
    level = SubjectLevel.query.filter(SubjectLevel.id == level_id).first()
    students = Student.query.join(Student.groups).options(contains_eager(Student.groups)).filter(
        Group.id == group_id).all()

    chapters_list = []
    if not chapter_id and not lesson_id:
        chapters = Chapter.query.filter(Chapter.level_id == level.id).order_by(Chapter.order).all()

        for chapter in chapters:
            chapter_percent = 0
            exercise_percent = 0
            student_exercises = StudentExercise.query.filter(StudentExercise.chapter_id == chapter.id,
                                                             StudentExercise.student_id.in_(
                                                                 [student_id.id for student_id in
                                                                  students])).all()
            exercises_blocks = ExerciseBlock.query.join(ExerciseBlock.exercise).options(
                contains_eager(ExerciseBlock.exercise)).filter(
                Exercise.level_id == level_id).filter(ExerciseBlock.exercise_answers != None,
                                                      Exercise.lesson != None,
                                                      Exercise.id.in_(
                                                          [exe.exercise.id for exe in student_exercises])).all()
            students_chapters_true = StudentChapter.query.filter(
                StudentChapter.student_id.in_([student_id.id for student_id in students]),
                StudentChapter.chapter_id == chapter.id, StudentChapter.finished == True).order_by(
                StudentChapter.id, StudentChapter.level_id == level_id).count()
            true_exercises = StudentExercise.query.filter(
                StudentExercise.student_id.in_([student_id.id for student_id in students]),
                StudentExercise.chapter_id == chapter.id,
                StudentExercise.block_id.in_([block.id for block in exercises_blocks]),
                StudentExercise.boolean == True).count()
            info = {
                "id": chapter.id,
                "name": chapter.name,
                "finished": f"{round((students_chapters_true / len(students)) * 100)}%",
                "exercises": f"{round((true_exercises / len(students)) * 100)}%",
                "students": []
            }
            students_chapters = StudentChapter.query.filter(
                StudentChapter.student_id.in_([student_id.id for student_id in students]),
                StudentChapter.chapter_id == chapter.id).order_by(
                StudentChapter.id).all()
            student_exercises = StudentExercise.query.filter(StudentExercise.chapter_id == chapter.id,
                                                             StudentExercise.student_id.in_(
                                                                 [student_id.id for student_id in
                                                                  students])).all()
            exercises_blocks = ExerciseBlock.query.join(ExerciseBlock.exercise).options(
                contains_eager(ExerciseBlock.exercise)).filter(
                Exercise.level_id == level_id).filter(ExerciseBlock.exercise_answers != None,
                                                      Exercise.lesson != None,
                                                      Exercise.id.in_(
                                                          [exe.exercise.id for exe in student_exercises])).all()
            exercise_answers = ExerciseAnswers.query.filter(
                ExerciseAnswers.block_id.in_([block.id for block in exercises_blocks])).all()
            all_lessons = Lesson.query.filter(Lesson.chapter_id == chapter.id).count()
            for student_chapter in students_chapters:
                true_exercises = StudentExercise.query.filter(
                    StudentExercise.student_id == student_chapter.student_id,
                    StudentExercise.chapter_id == chapter.id,
                    StudentExercise.block_id.in_([block.id for block in exercises_blocks]),
                    StudentExercise.boolean == True).count()
                student_lessons_true = StudentLesson.query.filter(
                    StudentLesson.student_id == student_chapter.student_id,
                    StudentLesson.chapter_id == chapter.id, StudentLesson.finished == True).count()
                chapter_percent += round((student_lessons_true / all_lessons) * 100) if all_lessons != 0 else 0
                exercise_percent += round((true_exercises / len(exercise_answers)) * 100) if exercise_answers else 0
                info['students'].append({
                    "id": chapter.id,
                    "student_chapter": student_chapter.id,
                    "percentage": student_chapter.percentage,
                    "student_name": student_chapter.student.user.name,
                    "student_surname": student_chapter.student.user.surname,
                    "student_id": student_chapter.student_id,
                    "exercises": f"{round((true_exercises / len(exercise_answers)) * 100) if exercise_answers else 0}%",
                    "finished": f"{round((student_lessons_true / all_lessons) * 100) if all_lessons else 0}%"
                })

            info['finished'] = f"{round(chapter_percent / len(students))}%"
            info['exercises'] = f"{round(exercise_percent / len(students))}%"
            chapters_list.append(info)
        return jsonify({
            "data": {
                "all_chapters": len(chapters),
                "chapters_list": chapters_list,

            }
        })
    elif chapter_id and not lesson_id:
        chapter = Chapter.query.filter(Chapter.id == chapter_id).first()
        print('chapter')
        all_lessons = Lesson.query.filter(Lesson.chapter_id == chapter.id).order_by(Lesson.order).all()
        for lesson in all_lessons:
            lesson_percent = 0
            exercise_percent = 0
            student_exercises = StudentExercise.query.filter(StudentExercise.lesson_id == lesson.id,
                                                             StudentExercise.student_id.in_(
                                                                 [student_id.id for student_id in
                                                                  students])).all()
            exercises_blocks = ExerciseBlock.query.join(ExerciseBlock.exercise).options(
                contains_eager(ExerciseBlock.exercise)).filter(
                Exercise.level_id == level_id).filter(ExerciseBlock.exercise_answers != None,
                                                      Exercise.lesson != None,
                                                      Exercise.id.in_(
                                                          [exe.exercise.id for exe in student_exercises])).all()
            students_lessons_true = StudentLesson.query.filter(
                StudentLesson.student_id.in_([student_id.id for student_id in students]),
                StudentLesson.lesson_id == lesson.id, StudentLesson.finished == True).order_by(
                StudentLesson.id).count()
            true_exercises = StudentExercise.query.filter(
                StudentExercise.student_id.in_([student_id.id for student_id in students]),
                StudentExercise.chapter_id == chapter.id,
                StudentExercise.block_id.in_([block.id for block in exercises_blocks]),
                StudentExercise.boolean == True).count()
            info = {
                "id": lesson.id,
                "name": lesson.name,
                "finished": f"{round((students_lessons_true / len(students)) * 100)}%",
                "exercises": f"{round((true_exercises / len(exercises_blocks)) * 100) if exercises_blocks else 0}%",
                "students": []
            }
            students_lessons = StudentLesson.query.filter(StudentLesson.lesson_id == lesson.id,
                                                          StudentLesson.student_id.in_(
                                                              [student_id.id for student_id in students])).order_by(
                StudentLesson.order).all()
            for student_lesson in students_lessons:
                students_lessons_true = StudentLesson.query.filter(
                    StudentLesson.student_id == student_lesson.student_id,
                    StudentLesson.lesson_id == lesson.id, StudentLesson.finished == True).order_by(
                    StudentLesson.id).first()
                if students_lessons_true:
                    lesson_percent += 100
                exercise_percent += student_lesson.percentage
                info['students'].append({
                    "student_name": student_lesson.student.user.name,
                    "student_surname": student_lesson.student.user.surname,
                    "student_id": student_lesson.student_id,
                    "exercises": f"{round(student_lesson.percentage)}%",
                    "finished": "100%" if student_lesson.finished else "0%"
                })
            info['finished'] = f"{round(lesson_percent / len(students))}%"
            info['exercises'] = f"{round(exercise_percent / len(students))}%"
            chapters_list.append(info)
        return jsonify({
            "data": {
                "lesson_list": chapters_list,

            }
        })
    else:
        student_lessons = StudentLesson.query.filter(StudentLesson.lesson_id == lesson_id, StudentLesson.student_id.in_(
            [student_id.id for student_id in students])).order_by(StudentLesson.order).all()
        for les in student_lessons:
            chapters_list.append({
                "percentage": les.percentage,
                "student_name": les.student.user.name,
                "student_surname": les.student.user.surname,
                "student_id": les.student_id,
                "exercises": f"{round(les.percentage)}%",
                "finished": les.finished,
                "status": True if les.finished == True > 0 else False
            })

        return jsonify({
            "data": {
                "lesson_list": chapters_list,

            }
        })


@app.route(f'{api}/student_exercise_block/<lesson_id>/<student_id>')
def student_exercise_block(lesson_id, student_id):
    lesson = StudentLesson.query.filter(StudentLesson.lesson_id == lesson_id,
                                        StudentLesson.student_id == student_id).first()
    exercise_block = StudentExerciseBlock.query.filter(StudentExerciseBlock.lesson_id == lesson_id,
                                                       StudentExerciseBlock.student_id == student_id,
                                                       ).order_by(
        StudentExerciseBlock.id).all()
    student_exercises = StudentExercise.query.filter(StudentExercise.lesson_id == lesson_id,
                                                     StudentExercise.student_id == student_id).first()
    student_lesson_archive = StudentLessonArchive.query.filter(
        StudentLessonArchive.student_lesson == lesson.id, StudentLessonArchive.student_id == student_id,
        StudentLessonArchive.status == False, StudentLessonArchive.lesson_id == lesson_id).first()

    data = lesson.degree_convert("exc",
                                 student_lesson_archive_id=student_lesson_archive.id) if student_exercises else ""

    return jsonify({
        "data": {

            "lesson": data,
            "blocks": iterate_models(exercise_block)
        }
    })
