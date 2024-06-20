from backend.models.basic_model import StudentLesson, StudentChapter, db, StudentLevel, StudentSubject, Lesson, \
    StudentExercise, StudentLessonArchive


def update_student_datas(student, lesson_id):
    student_lesson = StudentLesson.query.filter(StudentLesson.lesson_id == lesson_id,
                                                StudentLesson.student_id == student.id).first()
    lesson = Lesson.query.filter(Lesson.id == student_lesson.lesson_id).first()
    if len(lesson.exercises) == 0:
        StudentLesson.query.filter(StudentLesson.id == lesson_id).update({
            "finished": True
        })
        db.session.commit()

    student_lessons_true = StudentLesson.query.filter(StudentLesson.level_id == student_lesson.level_id,
                                                      StudentLesson.finished == True,
                                                      StudentLesson.student_id == student.id).count()
    student_lessons = StudentLesson.query.filter(StudentLesson.level_id == student_lesson.level_id,
                                                 StudentLesson.student_id == student.id).count()
    student_chapter = StudentChapter.query.filter(StudentChapter.student_id == student.id,
                                                  StudentChapter.id == student_lesson.self_chapter_id).first()

    if student_lessons_true == student_lessons:
        student_chapter.finished = True
        db.session.commit()

    student_chapter_true = StudentChapter.query.filter(StudentChapter.student_id == student.id,
                                                       StudentChapter.level_id == student_lesson.level_id,
                                                       StudentChapter.finished == True).count()
    student_chapters = StudentChapter.query.filter(StudentChapter.student_id == student.id,
                                                   StudentChapter.level_id == student_lesson.level_id).count()
    student_level = StudentLevel.query.filter(StudentLevel.level_id == student_lesson.level_id,
                                              StudentLevel.student_id == student.id).first()
    if student_chapter_true == student_chapters:
        student_level.finished = True
        db.session.commit()

    student_level_true = StudentLevel.query.filter(StudentLevel.subject_id == student_lesson.lesson.subject_id,
                                                   StudentLevel.student_id == student.id,
                                                   StudentLevel.finished == True).count()
    student_levels = StudentLevel.query.filter(StudentLevel.subject_id == student_lesson.lesson.subject_id,
                                               StudentLevel.student_id == student.id,
                                               ).count()
    student_subject = StudentSubject.query.filter(StudentSubject.student_id == student.id,
                                                  StudentSubject.subject_id == student_lesson.lesson.subject_id).first()

    if student_level_true == student_levels:
        student_subject.finished = True
        db.session.commit()


def update_ratings(student, lesson_id):
    student_lesson = StudentLesson.query.filter(StudentLesson.lesson_id == lesson_id,
                                                StudentLesson.student_id == student.id).first()
    student_lesson_archive = StudentLessonArchive.query.filter(StudentLessonArchive.student_id == student.id,
                                                               StudentLessonArchive.lesson_id == lesson_id,
                                                               StudentLessonArchive.status == True).order_by(
        StudentLessonArchive.id).first()
    if student_lesson_archive:
        student_exercises_true = StudentExercise.query.filter(StudentExercise.student_id == student.id,
                                                              StudentExercise.boolean == True,
                                                              StudentExercise.student_lesson_archive_id == student_lesson_archive.id,
                                                              StudentExercise.lesson_id == lesson_id).count()

        student_exercises = StudentExercise.query.filter(StudentExercise.student_id == student.id,
                                                         StudentExercise.student_lesson_archive_id == student_lesson_archive.id,
                                                         StudentExercise.lesson_id == lesson_id).count()
    else:
        student_exercises_true = StudentExercise.query.filter(StudentExercise.student_id == student.id,
                                                              StudentExercise.boolean == True,

                                                              StudentExercise.lesson_id == lesson_id).count()

        student_exercises = StudentExercise.query.filter(StudentExercise.student_id == student.id,
                                                         StudentExercise.lesson_id == lesson_id).count()
    student_exercises_all = StudentExercise.query.filter(StudentExercise.student_id == student.id,
                                                         StudentExercise.lesson_id == lesson_id).all()
    lesson = Lesson.query.filter(Lesson.id == lesson_id).first()
    exercise_id = list(set([ex.exercise_id for ex in student_exercises_all]))

    if len(lesson.exercises) == len(exercise_id):
        student_lesson.finished = True
        db.session.commit()

    percentage = round((student_exercises_true / student_exercises) * 100) if student_exercises_true else 0

    student_lesson.percentage = percentage

    db.session.commit()

    student_lesson = StudentLesson.query.filter(StudentLesson.lesson_id == lesson_id,
                                                StudentLesson.student_id == student.id).first()
    student_lessons = StudentLesson.query.filter(StudentLesson.level_id == student_lesson.level_id,
                                                 StudentLesson.student_id == student.id
                                                 ).count()
    student_lessons_finished = StudentLesson.query.filter(StudentLesson.level_id == student_lesson.level_id,
                                                          StudentLesson.percentage == 100).count()

    level_percentage = round((student_lessons_finished / student_lessons) * 100)

    student_chapter = StudentChapter.query.filter(StudentChapter.level_id == student_lesson.level_id,
                                                  StudentChapter.id == student_lesson.self_chapter_id,
                                                  StudentChapter.student_id == student.id).first()
    student_chapter.percentage = level_percentage
    db.session.commit()

    student_chapters = StudentChapter.query.filter(StudentChapter.level_id == student_lesson.level_id,
                                                   StudentChapter.student_id == student.id
                                                   ).count()
    student_chapters_finished = StudentLesson.query.filter(StudentChapter.level_id == student_lesson.level_id,
                                                           StudentChapter.student_id == student.id,
                                                           StudentChapter.percentage == 100).count()
    student_level = StudentLevel.query.filter(StudentLevel.level_id == student_lesson.level_id,
                                              StudentLevel.student_id == student.id).first()

    level_percentage = round((student_chapters_finished / student_chapters) * 100)
    student_level.percentage = level_percentage
    db.session.commit()

    student_levels = StudentLevel.query.filter(StudentLevel.subject_id == student_lesson.lesson.subject_id,
                                               StudentLevel.student_id == student.id
                                               ).count()
    student_levels_finished = StudentLevel.query.filter(StudentLevel.subject_id == student_lesson.lesson.subject_id,
                                                        StudentLevel.student_id == student.id,
                                                        StudentLevel.percentage == 100).count()
    student_subject = StudentSubject.query.filter(StudentSubject.subject_id == student_lesson.lesson.subject_id,
                                                  StudentLevel.student_id == student.id).first()

    level_percentage = round((student_levels_finished / student_levels) * 100)
    student_subject.percentage = level_percentage
    db.session.commit()
