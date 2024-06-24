import datetime

from backend.models.basic_model import db, Column, relationship, Integer, String, ForeignKey, Float, Boolean, JSON, \
    func, DateTime


class Subject(db.Model):
    __tablename__ = "subject"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    file_id = Column(Integer, ForeignKey('file.id'))
    desc = Column(String)
    levels = relationship("SubjectLevel", backref="subject", order_by="SubjectLevel.id")
    answer = relationship('ExerciseAnswers', backref="subject", order_by="ExerciseAnswers.id")
    lesson = relationship('Lesson', backref="subject", order_by="Lesson.id")
    exercise = relationship('Exercise', backref="subject", order_by="Exercise.id")
    student_question = relationship("StudentQuestion", lazy="select", order_by="StudentQuestion.id")
    donelessons = relationship('StudentExercise', backref="subject", order_by="StudentExercise.id")
    studentsubject = relationship('StudentSubject', backref="subject", order_by="StudentSubject.id")
    certificate = relationship('Certificate', backref="subject", order_by="Certificate.id")
    groups = relationship("Group", backref="subject", order_by="Group.id")
    disabled = Column(Boolean, default=False)

    def convert_json(self, entire=False):
        if self.groups or self.lesson or self.levels or self.exercise:
            deleted = False
        else:
            deleted = True
        if not entire:
            info = {
                "id": self.id,
                "name": self.name,
                "img": None,
                "desc": self.desc,
                "disabled": self.disabled,
                "status_deleted": deleted
            }
            if self.file and self.file.url:
                info['img'] = self.file.url
            return info
        info = {
            "id": self.id,
            "name": self.name,
            "img": None,
            "desc": self.desc,
            "disabled": self.disabled,
            "status_deleted": deleted,
            "levels": []
        }
        if self.file and self.file.url:
            info['img'] = self.file.url
        for level in self.levels:
            level_info = {
                "id": level.id,
                "name": level.name,
                "disabled": level.disabled
            }
            info['level'].append(level_info)
        return info

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


class LevelCategory(db.Model):
    __tablename__ = "level_category"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    ot = Column(Float)
    do = Column(Float)
    # students = relationship("Student", backref="level", order_by="Student.id", lazy="select")


class SubjectLevel(db.Model):
    __tablename__ = "subject_level"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    desc = Column(String)
    subject_id = Column(Integer, ForeignKey("subject.id"))
    disabled = Column(Boolean, default=False)
    lesson = relationship('Lesson', backref="subject_level", order_by="Lesson.id")
    student_lesson = relationship("StudentLesson", backref="subject_level", order_by="StudentLesson.id")
    exercise = relationship('Exercise', backref="subject_level", order_by="Exercise.id")
    donelessons = relationship("StudentExercise", backref="subject_level", order_by="StudentExercise.id")
    student_level = relationship('StudentLevel', backref="subject_level", order_by="StudentLevel.id")
    certificate = relationship('Certificate', backref="subject_level", order_by="Certificate.id")
    groups = relationship('Group', backref="subject_level", order_by="Group.id")
    chapters = relationship('Chapter', backref="subject_level", order_by="Chapter.id")
    student_question = relationship('StudentQuestion', backref="subject_level", order_by="StudentQuestion.id")

    def convert_json(self, entire=False):
        return {
            "id": self.id,
            "name": self.name,
            "subject": {
                "id": self.subject_id,
                "name": self.subject.name,
                "disabled": self.subject.disabled
            },
            "desc": self.desc,
            "disabled": self.disabled,

        }

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


class Chapter(db.Model):
    __tablename__ = "chapter"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    level_id = Column(Integer, ForeignKey("subject_level.id"))
    lesson = relationship('Lesson', backref="chapter", order_by="Lesson.order")
    order = Column(Integer)
    student_chapters = relationship("StudentChapter", backref='chapter', order_by="StudentChapter.id")
    disabled = Column(Boolean, default=False)

    def add(self):
        db.session.add(self)
        db.session.commit()

    def convert_json(self, entire=False):

        info = {
            "id": self.id,
            "chapter_id": f"chapter{self.id}",
            "name": self.name,
            "level": self.subject_level.convert_json(),
            "lessons": [],
            "finished": None,
            "percentage": None
        }
        if entire:
            for lesson in self.lesson:
                if lesson.disabled != True:
                    info['lessons'].append(lesson.convert_json())
        return info


class StudentChapter(db.Model):
    __tablename__ = "student_chapter"
    id = Column(Integer, primary_key=True)
    level_id = Column(Integer, ForeignKey("subject_level.id"))
    chapter_id = Column(Integer, ForeignKey('chapter.id'))
    student_id = Column(Integer, ForeignKey("student.id"))
    percentage = Column(Float, default=0)
    order = Column(Integer, default=0)
    finished = Column(Boolean, default=False)
    lesson = relationship("StudentLesson", backref="student_chapter", order_by="StudentLesson.order")

    def convert_json(self, entire=False):

        true_exercises = StudentExercise.query.filter(StudentExercise.student_id == self.student_id,
                                                      StudentExercise.student_chapter_id == self.id,
                                                      StudentExercise.boolean == True).count()
        false_exercises = StudentExercise.query.filter(StudentExercise.student_id == self.student_id,
                                                       StudentExercise.student_chapter_id == self.id,
                                                       StudentExercise.boolean == False).count()
        info = {
            "id": self.chapter.id,
            "chapter_id": f"chapter{self.chapter.id}",
            "name": self.chapter.name,
            "level": self.chapter.subject_level.convert_json(),
            "lessons": [],
            "finished": self.finished,
            "percentage": self.percentage,
            "student_name": self.student.user.name,
            "student_surname": self.student.user.surname,
            "true_exercises": true_exercises,
            "false_exercises": false_exercises
        }

        if entire:
            for lesson in self.lesson:
                if lesson.lesson.disabled != True:
                    info['lessons'].append(lesson.convert_json())
        return info

    def add(self):
        db.session.add(self)
        db.session.commit()


class Lesson(db.Model):
    __tablename__ = "lesson"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subject.id"))
    level_id = Column(Integer, ForeignKey("subject_level.id"))
    name = Column(String)
    exercises = relationship("Exercise", secondary="lesson_exercise", backref="lesson", order_by="Exercise.id")
    blocks = relationship("LessonBlock", backref="lesson", order_by="LessonBlock.order")
    student_lesson = relationship("StudentLesson", backref="lesson", order_by="StudentLesson.id")
    disabled = Column(Boolean, default=False)
    order = Column(Integer)
    chapter_id = Column(Integer, ForeignKey('chapter.id'))
    test_status = Column(Boolean, default=False)
    test_numbers = Column(Integer)

    def convert_json(self, entire=False):
        if entire:
            info = {
                "id": self.id,
                "name": self.name,
                "subject_id": self.subject.id,
                "subject_name": self.subject.name,
                "level_id": self.subject_level.id,
                "level_name": self.subject_level.name,
                "blocks": [],
                "order": self.order,
                "chapter_id": self.chapter_id,
                "is_test": self.test_status,
                "number_test": self.test_numbers
            }
            for block in self.blocks:
                block_info = {
                    "id": block.id,
                    "video_url": block.video_url,
                    "img": None,
                    "file": None,
                    "desc": block.desc,
                    "clone": block.clone,
                    "exercise_id": block.exercise_id,
                    "type": block.type_block,
                    "exercise_block": [],

                }
                if block.file_id:
                    if block.file.type_file == "img":
                        block_info['img'] = block.file.url
                    else:
                        block_info['file'] = block.file.convert_json()
                if block.exercise_id:
                    exercise = Exercise.query.filter(Exercise.id == block.exercise_id).first()
                    if exercise.random_status and self.test_status:
                        exercise_blocks = ExerciseBlock.query.filter(ExerciseBlock.exercise_id == exercise.id).order_by(
                            func.random()).limit(self.test_numbers).all()
                        for block_exercise in exercise_blocks:
                            ex_block = {
                                "id": block_exercise.id,
                                "answers": [],
                                'innerType': block_exercise.inner_type,
                                "clone": block_exercise.clone,
                                "type": block_exercise.component.name,
                                "img": "",
                                "audio_url": block_exercise.audio.url if block_exercise.audio else "",
                                "desc": block_exercise.desc,
                                "words_img": [],
                                "words_clone": block_exercise.for_words

                            }
                            block_images = ExerciseBlockImages.query.filter(
                                ExerciseBlockImages.block_id == block_exercise.id).order_by(
                                ExerciseBlockImages.id).all()
                            for img in block_images:
                                info_img = {
                                    "id": img.file.id,
                                    "img": img.file.url,
                                    "order": img.order,
                                    "type": img.type_image
                                }
                                ex_block['words_img'].append(info_img)
                            if block_exercise.img:
                                ex_block['img'] = block_exercise.img.url
                            answers = ExerciseAnswers.query.filter(ExerciseAnswers.block_id == block_exercise.id,
                                                                   ExerciseAnswers.exercise_id == block.exercise_id,
                                                                   ).order_by(
                                ExerciseAnswers.id).all()
                            for exe in answers:
                                img = None
                                if exe.file:
                                    img = exe.file.url
                                answer_info = {
                                    "id": exe.id,
                                    "desc": exe.desc,
                                    "order": exe.order,
                                    "img": img,
                                    "block_id": exe.block_id,
                                    "type_img": exe.type_img
                                }
                                ex_block['answers'].append(answer_info)
                            block_info['exercise_block'].append(ex_block)
                    else:
                        for block_exercise in exercise.block:

                            ex_block = {
                                "id": block_exercise.id,
                                "answers": [],
                                'innerType': block_exercise.inner_type,
                                "clone": block_exercise.clone,
                                "type": block_exercise.component.name,
                                "img": "",
                                "audio_url": block_exercise.audio.url if block_exercise.audio else "",
                                "desc": block_exercise.desc,
                                "words_img": [],
                                "words_clone": block_exercise.for_words

                            }
                            block_images = ExerciseBlockImages.query.filter(
                                ExerciseBlockImages.block_id == block_exercise.id).order_by(
                                ExerciseBlockImages.id).all()
                            for img in block_images:
                                info_img = {
                                    "id": img.file.id,
                                    "img": img.file.url,
                                    "order": img.order,
                                    "type": img.type_image
                                }
                                ex_block['words_img'].append(info_img)
                            if block_exercise.img:
                                ex_block['img'] = block_exercise.img.url
                            answers = ExerciseAnswers.query.filter(ExerciseAnswers.block_id == block_exercise.id,
                                                                   ExerciseAnswers.exercise_id == block.exercise_id,
                                                                   ).order_by(
                                ExerciseAnswers.id).all()
                            for exe in answers:
                                img = None
                                if exe.file:
                                    img = exe.file.url
                                answer_info = {
                                    "id": exe.id,
                                    "desc": exe.desc,
                                    "order": exe.order,
                                    "img": img,
                                    "block_id": exe.block_id,
                                    "type_img": exe.type_img
                                }
                                ex_block['answers'].append(answer_info)
                            block_info['exercise_block'].append(ex_block)
                info['blocks'].append(block_info)
            return info
        else:

            return {
                "id": self.id,
                "name": self.name,
                "subject_id": self.subject.id,
                "subject_name": self.subject.name,
                "level_id": self.subject_level.name,
                "order": self.order

            }

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


class LessonBlock(db.Model):
    __tablename__ = "lesson_block"
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey('lesson.id'))
    exercise_id = Column(Integer, ForeignKey('exercise.id'))
    video_url = Column(String)
    file_id = Column(Integer, ForeignKey('file.id'))
    desc = Column(String)
    clone = Column(JSON)
    type_block = Column(String)
    order = Column(Integer)

    def add_commit(self):
        db.session.add(self)
        db.session.commit()

    def delete_commit(self):
        db.session.delete(self)
        db.session.commit()


class ExerciseTypes(db.Model):
    __tablename__ = "exercise_types"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type_exercise = Column(String)
    exercises = relationship("Exercise", backref="exercise_types", order_by="Exercise.id")
    donelessons = relationship("StudentExercise", backref="exercise_types", order_by="StudentExercise.id")
    disabled = Column(Boolean, default=False)

    def convert_json(self, entire=False):
        return {
            "id": self.id,
            "del_status": False,
            "name": self.name,
            "type": self.type_exercise
        }

    def convert_json_check(self):
        return {
            "id": self.id,
            "del_status": True,
            "name": self.name,
            "type": self.type_exercise
        }

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


class Component(db.Model):
    __tablename__ = "component"
    id = Column(Integer, primary_key=True)
    type_component = Column(String)
    name = Column(String)
    exercise_blocks = relationship("ExerciseBlock", backref="component", order_by="ExerciseBlock.id")

    def convert_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "img": self.img,
            "desc": self.desc
        }

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


class Exercise(db.Model):
    __tablename__ = "exercise"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    subject_id = Column(Integer, ForeignKey("subject.id"))
    type_id = Column(Integer, ForeignKey('exercise_types.id'))
    level_id = Column(Integer, ForeignKey("subject_level.id"))
    block = relationship("ExerciseBlock", backref="exercise", lazy="select", order_by="ExerciseBlock.order")
    exercise_answers = relationship("ExerciseAnswers", backref="exercise", order_by="ExerciseAnswers.id")
    donelessons = relationship("StudentExercise", backref="exercise", order_by="StudentExercise.id")
    random_status = Column(Boolean, default=False)

    def add_commit(self):
        db.session.add(self)
        db.session.commit()

    def convert_json(self, entire=False):
        if entire:
            info = {
                "id": self.id,
                "name": self.name,
                "subject": {
                    "id": self.subject.id,
                    "name": self.subject.name
                },
                "type": {
                    "id": self.exercise_types.id,
                    "name": self.exercise_types.name,
                    "type": self.exercise_types.type_exercise

                },
                "level": {
                    "id": self.subject_level.id,
                    "name": self.subject_level.name
                },
                "block": [],
                "random": self.random_status
            }
            if self.random_status:
                exercise_blocks = ExerciseBlock.query.filter(ExerciseBlock.exercise_id == self.id).order_by(
                    func.random()).all()
                for block in exercise_blocks:
                    info_block = {
                        "id": block.id,
                        "desc": block.desc,
                        "clone": block.clone,
                        "type": block.component.name,
                        "img": None,
                        "audio": block.audio.url if block.audio else "",
                        "answers": [],
                        "innerType": block.inner_type,
                        "words_img": [],
                        "words_clone": block.for_words,

                    }
                    block_images = ExerciseBlockImages.query.filter(
                        ExerciseBlockImages.block_id == block.id).order_by(ExerciseBlockImages.id).all()
                    for img in block_images:
                        info_img = {
                            "id": img.file.id,
                            "img": img.file.url,
                            "order": img.order,
                            "type": img.type_image
                        }
                        info_block['words_img'].append(info_img)
                    if block.img:
                        info_block['img'] = block.img.url
                    info['block'].append(info_block)
                    for answers in block.exercise_answers:
                        img = None
                        if answers.file:
                            img = answers.file.url
                        info_answer = {
                            "id": answers.id,
                            "desc": answers.desc,
                            "order": answers.order,
                            "img": img,
                            "block_id": answers.block_id,
                            "type_img": answers.type_img
                        }
                        if answers.file:
                            info_answer['img'] = answers.file.url
                        info_block['answers'].append(info_answer)
            else:
                for block in self.block:
                    info_block = {
                        "id": block.id,
                        "desc": block.desc,
                        "clone": block.clone,
                        "type": block.component.name,
                        "img": None,
                        "audio": block.audio.url if block.audio else "",
                        "answers": [],
                        "innerType": block.inner_type,
                        "words_img": [],
                        "words_clone": block.for_words,

                    }
                    block_images = ExerciseBlockImages.query.filter(
                        ExerciseBlockImages.block_id == block.id).order_by(ExerciseBlockImages.id).all()
                    for img in block_images:
                        info_img = {
                            "id": img.file.id,
                            "img": img.file.url,
                            "order": img.order,
                            "type": img.type_image
                        }
                        info_block['words_img'].append(info_img)
                    if block.img:
                        info_block['img'] = block.img.url
                    info['block'].append(info_block)
                    for answers in block.exercise_answers:
                        img = None
                        if answers.file:
                            img = answers.file.url
                        info_answer = {
                            "id": answers.id,
                            "desc": answers.desc,
                            "order": answers.order,
                            "img": img,
                            "block_id": answers.block_id,
                            "type_img": answers.type_img
                        }
                        if answers.file:
                            info_answer['img'] = answers.file.url
                        info_block['answers'].append(info_answer)
            return info
        return {
            "id": self.id,
            "name": self.name,
            "subject": {
                "id": self.subject.id,
                "name": self.subject.name
            },
            "type": {
                "id": self.exercise_types.id,
                "name": self.exercise_types.name

            },
            "level": {
                "id": self.subject_level.id,
                "name": self.subject_level.name
            },
            "random": self.random_status,
            "block": [],

        }

    def delete_commit(self):
        db.session.delete(self)
        db.session.commit()


class ExerciseBlock(db.Model):
    __tablename__ = "exercise_block"
    id = Column(Integer, primary_key=True)
    desc = Column(String)
    exercise_id = Column(Integer, ForeignKey('exercise.id'))
    clone = Column(JSON())
    component_id = Column(Integer, ForeignKey('component.id'))
    audio_info = Column(Integer, ForeignKey('file.id'))
    img_info = Column(Integer, ForeignKey('file.id'))
    audio = relationship("File", foreign_keys=[audio_info], backref="file_audio")
    img = relationship("File", foreign_keys=[img_info], backref="file_img")
    exercise_answers = relationship("ExerciseAnswers", backref="exercise_block", order_by="ExerciseAnswers.id")
    student_exercises = relationship("StudentExercise", backref="exercise_block", order_by="StudentExercise.id")
    student_block = relationship("StudentExerciseBlock", backref="exercise_block", order_by="StudentExerciseBlock.id")
    inner_type = Column(String)
    order = Column(Integer)
    for_words = Column(JSON())

    def add_commit(self):
        db.session.add(self)
        db.session.commit()

    def delete_commit(self):
        db.session.delete(self)
        db.session.commit()


db.Table('lesson_exercise',
         db.Column('lesson_id', db.Integer, db.ForeignKey('lesson.id')),
         db.Column('exercise_id', db.Integer, db.ForeignKey('exercise.id'))
         )


class ExerciseAnswers(db.Model):
    __tablename__ = "exercise_answers"
    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey('exercise_types.id'))
    exercise_id = Column(Integer, ForeignKey('exercise.id'))
    subject_id = Column(Integer, ForeignKey('subject.id'))
    level_id = Column(Integer, ForeignKey("subject_level.id"))
    desc = Column(String)
    order = Column(Integer)
    file_id = Column(Integer, ForeignKey('file.id'))
    status = Column(Boolean, default=False)
    block_id = Column(Integer, ForeignKey('exercise_block.id'))
    type_img = Column(String)
    student_exercise = relationship("StudentExercise", backref="exercise_answer", order_by="StudentExercise.id")

    def convert_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "img": self.file.url,
            "desc": self.desc
        }

    def add_commit(self):
        db.session.add(self)
        db.session.commit()

    def delete_commit(self):
        db.session.delete(self)
        db.session.commit()


class StudentExercise(db.Model):
    __tablename__ = "student_exercise"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student.id"))
    lesson_id = Column(Integer, ForeignKey("lesson.id"))
    level_id = Column(Integer, ForeignKey("subject_level.id"))
    type_id = Column(Integer, ForeignKey("exercise_types.id"))
    subject_id = Column(Integer, ForeignKey("subject.id"))
    exercise_id = Column(Integer, ForeignKey("exercise.id"))
    boolean = Column(Boolean)
    block_id = Column(Integer, ForeignKey('exercise_block.id'))
    answer_id = Column(Integer, ForeignKey('exercise_answers.id'))
    value = Column(JSON())
    student_chapter_id = Column(Integer, ForeignKey('student_chapter.id'))
    chapter_id = Column(Integer, ForeignKey('chapter.id'))
    student_lesson_archive_id = Column(Integer, ForeignKey('student_lesson_archive.id'))

    def convert_json(self, entire=False):
        if entire:
            exercise = {
                "block": {
                    "id": self.block_id,
                    "answers": []
                }
            }
            for answer in self.exercise_block.exercise_answers:
                block_info = {
                    "id": answer.id,
                    "answer": answer.status
                }
                exercise['block']['answers'].append(block_info)
            return exercise

    def add_commit(self):
        db.session.add(self)
        db.session.commit()

    def delete_commit(self):
        db.session.delete(self)
        db.session.commit()


class ExerciseBlockImages(db.Model):
    __tablename__ = "exercise_block_images"
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('file.id'))
    block_id = Column(Integer, ForeignKey('exercise_block.id'))
    order = Column(Integer)
    type_image = Column(String)

    def add_commit(self):
        db.session.add(self)
        db.session.commit()

    def delete_commit(self):
        db.session.delete(self)
        db.session.commit()


class StudentLesson(db.Model):
    __tablename__ = "student_lesson"
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lesson.id"))
    student_id = Column(Integer, ForeignKey("student.id"))
    percentage = Column(Float, default=0)
    finished = Column(Boolean, default=False)
    level_id = Column(Integer, ForeignKey("subject_level.id"))
    order = Column(Integer, default=0)
    self_chapter_id = Column(Integer, ForeignKey('student_chapter.id'))
    chapter_id = Column(Integer, ForeignKey('chapter.id'))

    def degree_convert(self, type_block, student_lesson_archive_id=None):
        info = {
            "id": self.lesson.id,
            "name": self.lesson.name,
            "lesson_id": self.id,
            "subject_id": self.lesson.subject.id,
            "subject_name": self.lesson.subject.name,
            "level_id": self.lesson.subject_level.id,
            "level_name": self.subject_level.name,
            "blocks": [],
            "is_test": self.lesson.test_status,
            "number_test": self.lesson.test_numbers,

            "order": self.lesson.order,
            "percentage": self.percentage,
            "finished ": self.finished,
            "chapter_id": self.self_chapter_id
        }
        for block in self.lesson.blocks:
            if type_block == "exc":
                block_info = {
                    "id": block.id,
                    "video_url": block.video_url,
                    "img": None,
                    "file": None,
                    "desc": block.desc,
                    "clone": block.clone,
                    "exercise_id": block.exercise_id,
                    "type": block.type_block,
                    "exercise_block": []
                }

                exercise = Exercise.query.filter(Exercise.id == block.exercise_id).first()

                if exercise.block:
                    if exercise.random_status and self.lesson.test_status:
                        exercise_blocks = ExerciseBlock.query.filter(ExerciseBlock.exercise_id == exercise.id).order_by(
                            func.random).limit(self.lesson.test_numbers).all()
                        for block_exercise in exercise_blocks:
                            ex_block = {
                                "id": block_exercise.id,
                                "answers": [],
                                'innerType': block_exercise.inner_type,
                                "clone": block_exercise.clone,
                                "type": block_exercise.component.name,
                                "img": "",
                                "audio_url": block_exercise.audio.url if block_exercise.audio else "",
                                "desc": block_exercise.desc,
                                "words_img": [],
                                'isAnswered': False,
                                "words_clone": block_exercise.for_words
                            }
                            if not student_lesson_archive_id:
                                student_exercise = StudentExercise.query.filter(
                                    StudentExercise.lesson_id == self.lesson_id,

                                    StudentExercise.block_id == block_exercise.id,
                                    StudentExercise.exercise_id == block.exercise_id,
                                    StudentExercise.student_id == self.student_id).order_by(
                                    StudentExercise.id).all()
                            else:
                                student_exercise = StudentExercise.query.filter(
                                    StudentExercise.lesson_id == self.lesson_id,
                                    StudentExercise.student_lesson_archive_id == student_lesson_archive_id,
                                    StudentExercise.block_id == block_exercise.id,
                                    StudentExercise.exercise_id == block.exercise_id,
                                    StudentExercise.student_id == self.student_id).order_by(
                                    StudentExercise.id).all()
                            for exe in student_exercise:
                                info_answer = {
                                    "id": exe.id,
                                    "desc": exe.exercise_answer.desc,
                                    "order": exe.exercise_answer.order,
                                    "img": None,
                                    "block_id": exe.exercise_answer.block_id,
                                    "type_img": exe.exercise_answer.type_img,
                                    'status': exe.boolean,
                                    'value': exe.value,
                                }
                                if exe.exercise_answer.file:
                                    info_answer['img'] = exe.exercise_answer.file.url
                                ex_block['isAnswered'] = True
                                ex_block['answers'].append(info_answer)

                            block_info['exercise_block'].append(ex_block)
                        info['blocks'].append(block_info)
                    else:
                        for block_exercise in exercise.block:
                            ex_block = {
                                "id": block_exercise.id,
                                "answers": [],
                                'innerType': block_exercise.inner_type,
                                "clone": block_exercise.clone,
                                "type": block_exercise.component.name,
                                "img": "",
                                "audio_url": block_exercise.audio.url if block_exercise.audio else "",
                                "desc": block_exercise.desc,
                                "words_img": [],
                                'isAnswered': False,
                                "words_clone": block_exercise.for_words
                            }
                            student_exercise = StudentExercise.query.filter(
                                StudentExercise.lesson_id == self.lesson_id,

                                StudentExercise.block_id == block_exercise.id,
                                StudentExercise.exercise_id == block.exercise_id,
                                StudentExercise.student_id == self.student_id).order_by(
                                StudentExercise.id).all()
                            for exe in student_exercise:
                                info_answer = {
                                    "id": exe.id,
                                    "desc": exe.exercise_answer.desc,
                                    "order": exe.exercise_answer.order,
                                    "img": None,
                                    "block_id": exe.exercise_answer.block_id,
                                    "type_img": exe.exercise_answer.type_img,
                                    'status': exe.boolean,
                                    'value': exe.value,
                                }
                                if exe.exercise_answer.file:
                                    info_answer['img'] = exe.exercise_answer.file.url
                                ex_block['isAnswered'] = True
                                ex_block['answers'].append(info_answer)

                            block_info['exercise_block'].append(ex_block)
                    info['blocks'].append(block_info)
        return info

    def convert_json(self, entire=False, student_lesson_archive_id=None):
        if entire:
            info = {
                "id": self.lesson.id,
                "name": self.lesson.name,
                "lesson_id": self.id,
                "subject_id": self.lesson.subject.id,
                "subject_name": self.lesson.subject.name,
                "level_id": self.lesson.subject_level.id,
                "level_name": self.subject_level.name,
                "blocks": [],
                "order": self.lesson.order,
                "percentage": self.percentage,
                "finished ": self.finished,
                "chapter_id": self.self_chapter_id
            }

            for block in self.lesson.blocks:
                block_info = {
                    "id": block.id,
                    "video_url": block.video_url,
                    "img": None,
                    "file": None,
                    "desc": block.desc,
                    "clone": block.clone,
                    "exercise_id": block.exercise_id,
                    "type": block.type_block,
                    "exercise_block": []
                }
                if block.file_id:
                    if block.file.type_file == "img":
                        block_info['img'] = block.file.url
                    else:
                        block_info['file'] = block.file.url
                if block.exercise_id:
                    exercise = Exercise.query.filter(Exercise.id == block.exercise_id).first()
                    if exercise.random_status:
                        exercise_blocks = ExerciseBlock.query.filter(ExerciseBlock.exercise_id == exercise.id).order_by(
                            func.random()).all()
                        for block_exercise in exercise_blocks:
                            ex_block = {
                                "id": block_exercise.id,
                                "answers": [],
                                'innerType': block_exercise.inner_type,
                                "clone": block_exercise.clone,
                                "type": block_exercise.component.name,
                                "img": "",
                                "audio_url": block_exercise.audio.url if block_exercise.audio else "",
                                "desc": block_exercise.desc,
                                "words_img": [],
                                'isAnswered': False,
                                "words_clone": block_exercise.for_words

                            }
                            block_images = ExerciseBlockImages.query.filter(
                                ExerciseBlockImages.block_id == block_exercise.id).order_by(
                                ExerciseBlockImages.id).all()
                            for img in block_images:
                                info_img = {
                                    "id": img.file.id,
                                    "img": img.file.url,
                                    "order": img.order,
                                    "type": img.type_image
                                }
                                ex_block['words_img'].append(info_img)
                            if block_exercise.img:
                                ex_block['img'] = block_exercise.img.url

                            exercise_answers = ExerciseAnswers.query.filter(
                                ExerciseAnswers.exercise_id == block.exercise_id,
                                ExerciseAnswers.block_id == block_exercise.id).order_by(ExerciseAnswers.id).all()
                            if not student_lesson_archive_id:
                                student_exercise = StudentExercise.query.filter(
                                    StudentExercise.lesson_id == self.lesson_id,

                                    StudentExercise.block_id == block_exercise.id,
                                    StudentExercise.exercise_id == block.exercise_id,
                                    StudentExercise.student_id == self.student_id).order_by(
                                    StudentExercise.id).all()
                            else:
                                student_exercise = StudentExercise.query.filter(
                                    StudentExercise.lesson_id == self.lesson_id,
                                    StudentExercise.student_lesson_archive_id == student_lesson_archive_id,
                                    StudentExercise.block_id == block_exercise.id,
                                    StudentExercise.exercise_id == block.exercise_id,
                                    StudentExercise.student_id == self.student_id).order_by(
                                    StudentExercise.id).all()
                            if student_exercise:
                                for exe in student_exercise:
                                    info_answer = {
                                        "id": exe.id,
                                        "desc": exe.exercise_answer.desc,
                                        "order": exe.exercise_answer.order,
                                        "img": None,
                                        "block_id": exe.exercise_answer.block_id,
                                        "type_img": exe.exercise_answer.type_img,
                                        'status': exe.boolean,
                                        'value': exe.value,
                                    }
                                    if exe.exercise_answer.file:
                                        info_answer['img'] = exe.exercise_answer.file.url
                                    ex_block['isAnswered'] = True if student_lesson_archive_id else False
                                    ex_block['answers'].append(info_answer)
                            else:
                                for exe in exercise_answers:
                                    info_answer = {
                                        "id": exe.id,
                                        "desc": exe.desc,
                                        "order": exe.order,
                                        "img": None,
                                        "block_id": exe.block_id,
                                        "type_img": exe.type_img,
                                    }
                                    if exe.file:
                                        info_answer['img'] = exe.file.url
                                    ex_block['answers'].append(info_answer)
                            block_info['exercise_block'].append(ex_block)
                    else:
                        for block_exercise in exercise.block:
                            ex_block = {
                                "id": block_exercise.id,
                                "answers": [],
                                'innerType': block_exercise.inner_type,
                                "clone": block_exercise.clone,
                                "type": block_exercise.component.name,
                                "img": "",
                                "audio_url": block_exercise.audio.url if block_exercise.audio else "",
                                "desc": block_exercise.desc,
                                "words_img": [],
                                'isAnswered': False,
                                "words_clone": block_exercise.for_words

                            }
                            block_images = ExerciseBlockImages.query.filter(
                                ExerciseBlockImages.block_id == block_exercise.id).order_by(
                                ExerciseBlockImages.id).all()
                            for img in block_images:
                                info_img = {
                                    "id": img.file.id,
                                    "img": img.file.url,
                                    "order": img.order,
                                    "type": img.type_image
                                }
                                ex_block['words_img'].append(info_img)
                            if block_exercise.img:
                                ex_block['img'] = block_exercise.img.url

                            exercise_answers = ExerciseAnswers.query.filter(
                                ExerciseAnswers.exercise_id == block.exercise_id,
                                ExerciseAnswers.block_id == block_exercise.id).order_by(ExerciseAnswers.id).all()
                            if not student_lesson_archive_id:
                                student_exercise = StudentExercise.query.filter(
                                    StudentExercise.lesson_id == self.lesson_id,
                                    StudentExercise.block_id == block_exercise.id,
                                    StudentExercise.exercise_id == block.exercise_id,
                                    StudentExercise.student_id == self.student_id).order_by(
                                    StudentExercise.id).all()
                            else:
                                student_exercise = StudentExercise.query.filter(
                                    StudentExercise.lesson_id == self.lesson_id,
                                    StudentExercise.student_lesson_archive_id == student_lesson_archive_id,
                                    StudentExercise.block_id == block_exercise.id,
                                    StudentExercise.exercise_id == block.exercise_id,
                                    StudentExercise.student_id == self.student_id).order_by(
                                    StudentExercise.id).all()
                            if student_exercise:
                                for exe in student_exercise:
                                    info_answer = {
                                        "id": exe.id,
                                        "desc": exe.exercise_answer.desc,
                                        "order": exe.exercise_answer.order,
                                        "img": None,
                                        "block_id": exe.exercise_answer.block_id,
                                        "type_img": exe.exercise_answer.type_img,
                                        'status': exe.boolean,
                                        'value': exe.value,
                                    }
                                    if exe.exercise_answer.file:
                                        info_answer['img'] = exe.exercise_answer.file.url
                                    ex_block['isAnswered'] = True if student_lesson_archive_id else False
                                    ex_block['answers'].append(info_answer)
                            else:
                                for exe in exercise_answers:
                                    info_answer = {
                                        "id": exe.id,
                                        "desc": exe.desc,
                                        "order": exe.order,
                                        "img": None,
                                        "block_id": exe.block_id,
                                        "type_img": exe.type_img,
                                    }
                                    if exe.file:
                                        info_answer['img'] = exe.file.url
                                    ex_block['answers'].append(info_answer)
                            block_info['exercise_block'].append(ex_block)
                info['blocks'].append(block_info)

            return info
        return {
            "id": self.lesson.id,
            "lesson_id": self.id,
            "name": self.lesson.name,
            "subject_id": self.lesson.subject.id,
            "subject_name": self.lesson.subject.name,
            "level_id": self.subject_level.name,
            "order": self.lesson.order,
            "percentage": self.percentage,
            "finished": self.finished

        }

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


class StudentLessonArchive(db.Model):
    __tablename__ = "student_lesson_archive"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('student.id'))
    lesson_id = Column(Integer, ForeignKey("lesson.id"))
    student_lesson = Column(Integer, ForeignKey('student_lesson.id'))
    date = Column(DateTime, default=datetime.datetime.now())
    status = Column(Boolean, default=False)
    reset_date = Column(DateTime)

    def convert_json(self, entire=False):
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "reset_date": self.reset_date.strftime("%Y-%m-%d"),
            "status": self.status,
            "id": self.id
        }

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


class StudentExerciseBlock(db.Model):
    __tablename__ = "student_exercise_block"
    id = Column(Integer, primary_key=True)
    exercise_id = Column(Integer, ForeignKey('exercise.id'))
    block_id = Column(Integer, ForeignKey('exercise_block.id'))
    clone = Column(JSON())
    student_id = Column(Integer, ForeignKey('student.id'))
    lesson_id = Column(Integer, ForeignKey("lesson.id"))
    chapter_id = Column(Integer, ForeignKey('chapter.id'))
    student_lesson_archive_id = Column(Integer, ForeignKey('student_lesson_archive.id'))

    def convert_json(self, entire=False):
        ex_block = {
            "id": self.exercise_block.id,
            "answers": [],
            'innerType': self.exercise_block.inner_type,
            "clone": self.exercise_block.clone,
            "type": self.exercise_block.component.name,
            "img": "",
            "audio_url": self.exercise_block.audio.url if self.exercise_block.audio else "",
            "desc": self.exercise_block.desc,
            "words_img": [],
            'isAnswered': False,
            "words_clone": self.exercise_block.for_words

        }
        block_images = ExerciseBlockImages.query.filter(
            ExerciseBlockImages.block_id == self.exercise_block.id).order_by(ExerciseBlockImages.id).all()
        for img in block_images:
            info_img = {
                "id": img.file.id,
                "img": img.file.url,
                "order": img.order,
                "type": img.type_image
            }
            ex_block['words_img'].append(info_img)
        if self.exercise_block.img:
            ex_block['img'] = self.exercise_block.img.url

        student_exercise = StudentExercise.query.filter(
            StudentExercise.block_id == self.exercise_block.id,
            StudentExercise.exercise_id == self.exercise_block.exercise_id,
            StudentExercise.student_id == self.student_id,
            StudentExercise.student_lesson_archive_id == self.student_lesson_archive_id).order_by(
            StudentExercise.id).all()

        for exe in student_exercise:
            info_answer = {
                "id": exe.id,
                "desc": exe.exercise_answer.desc,
                "order": exe.exercise_answer.order,
                "img": None,
                "block_id": exe.exercise_answer.block_id,
                "type_img": exe.exercise_answer.type_img,
                'status': exe.boolean,
                'value': exe.value,

            }
            if exe.exercise_answer.file:
                info_answer['img'] = exe.exercise_answer.file.url
            ex_block['isAnswered'] = True
            ex_block['answers'].append(info_answer)
        return ex_block

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


class StudentLevel(db.Model):
    __tablename__ = "student_level"
    id = Column(Integer, primary_key=True)
    level_id = Column(Integer, ForeignKey("subject_level.id"))
    student_id = Column(Integer, ForeignKey("student.id"))
    percentage = Column(Float, default=0)
    group_id = Column(Integer, ForeignKey('group.id'))
    finished = Column(Boolean, default=False)
    subject_id = Column(Integer, ForeignKey('subject.id'))
    disabled = Column(Boolean, default=False)

    def convert_json(self, entire=False):
        chapters_finished = StudentChapter.query.filter(StudentChapter.student_id == self.student_id,
                                                        StudentChapter.level_id == self.level_id,
                                                        StudentChapter.finished == True).count()
        chapters = StudentChapter.query.filter(StudentChapter.student_id == self.student_id,
                                               StudentChapter.level_id == self.level_id,
                                               ).count()

        levels_finished = StudentLevel.query.filter(StudentLevel.student_id == self.student_id,
                                                    StudentLevel.subject_id == self.subject_id,
                                                    StudentLevel.finished == True).count()
        levels = StudentLevel.query.filter(StudentLevel.student_id == self.student_id,
                                           StudentLevel.subject_id == self.subject_id,
                                           ).count()
        return {
            "id": self.subject_level.id,
            "percentage": self.percentage,
            "finished": self.finished,
            "finished_percentage": round((chapters_finished / chapters) * 100) if chapters else 0,
            "level_id": self.id,
            "name": self.subject_level.name,
            "subject": {
                "id": self.subject_level.subject_id,
                "name": self.subject_level.subject.name,
                "disabled": self.subject_level.subject.disabled,
                "finished_percentage": round((levels_finished / levels) * 100)
            },
            "desc": self.subject_level.desc,
            "disabled": self.subject_level.disabled,
        }

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


class StudentSubject(db.Model):
    __tablename__ = "student_subject"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subject.id"))
    student_id = Column(Integer, ForeignKey("student.id"))
    percentage = Column(Integer, default=0)
    finished = Column(Boolean, default=False)

    def convert_json(self, entire=False):
        levels_finished = StudentLevel.query.filter(StudentLevel.student_id == self.student_id,
                                                    StudentLevel.subject_id == self.subject_id,
                                                    StudentLevel.finished == True).count()
        levels = StudentLevel.query.filter(StudentLevel.student_id == self.student_id,
                                           StudentLevel.subject_id == self.subject_id,
                                           ).count()
        return {
            "id": self.subject_id,
            "name": self.subject.name,
            "img": self.subject.file.url if self.subject.file else None,
            "percentage": self.percentage,
            "finished": self.finished,
            "finished_percentage": round((levels_finished / levels) * 100) if levels else 0,
            "levels": [{
                "id": level.id,
                "name": level.name,
                "disabled": level.disabled
            } for level in self.subject.levels]

        }

    def add_commit(self):
        db.session.add(self)
        db.session.commit()
