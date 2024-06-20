from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import *
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, functions
from sqlalchemy.dialects.postgresql import ARRAY

db = SQLAlchemy()


def db_setup(app):
    app.config.from_object('backend.models.config')
    db.app = app
    db.init_app(app)
    Migrate(app, db)
    return db


class Location(db.Model):
    __tablename__ = "location"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    platform_id = Column(Integer)
    users = relationship("User", backref="location", order_by="User.id")

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


class Role(db.Model):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True)
    role = Column(String)
    type = Column(String)
    platform_id = Column(Integer)
    user = relationship('User', backref="role", uselist=False)

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


class User(db.Model):
    id = Column(Integer, primary_key=True)
    __tablename__ = "user"
    username = Column(String)
    name = Column(String)
    surname = Column(String)
    file_id = Column(Integer, ForeignKey('file.id'))
    balance = Column(Integer)
    password = Column(String)
    platform_id = Column(Integer)
    age = Column(Integer)
    student = relationship('Student', backref='user', uselist=False, order_by="Student.id", lazy="select")
    teacher = relationship("Teacher", backref="user", order_by="Teacher.id", lazy="select")
    question_answers = relationship('QuestionAnswers', backref='user', order_by="QuestionAnswers.id", lazy="dynamic")
    question_answer_comment = relationship('QuestionAnswerComment', backref='user', order_by="QuestionAnswerComment.id",
                                           lazy="dynamic")
    location_id = Column(Integer, ForeignKey('location.id'))
    role_id = Column(Integer, ForeignKey('role.id'))
    certificate = relationship("Certificate", backref="user", order_by="Certificate.id")
    phone = Column(String)
    born_day = Column(Integer)
    born_month = Column(Integer)
    born_year = Column(Integer)
    father_name = Column(String)
    parent_phone = Column(String)
    user_id = Column(String, unique=True)
    observer = Column(Boolean, default=False)

    def convert_json(self):
        img = None
        if self.file:
            img = self.file.url
        day = self.born_day
        if len(str(self.born_day)) == 1:
            day = "0" + str(self.born_day)
        month = self.born_month
        if len(str(self.born_day)) == 1:
            month = "0" + str(self.born_month)
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "username": self.username,
            "balance": self.balance,
            "age": self.age,
            "role": self.role.role,
            "father_name": self.father_name,
            "parent_phone": self.parent_phone,
            "born_date": f'{day}-{month}-{self.born_year}',
            "phone": self.phone,
            "platform_id": self.platform_id,
            "location_id": self.location_id,
            "platform_location": self.location.platform_id,
            "observer": self.observer
        }

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


class Student(db.Model):
    __tablename__ = "student"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    debtor = Column(Integer)
    student_question = relationship("StudentQuestion", lazy="select", order_by="StudentQuestion.id")
    donelesson = relationship("StudentExercise", backref="student", order_by="StudentExercise.id")
    groups = relationship("Group", secondary="student_group", backref="student", order_by="Group.id")
    studentlesson = relationship("StudentLesson", backref="student", order_by="StudentLesson.id")
    subject_level = relationship("StudentLevel", backref="student", order_by="StudentLevel.id")
    studentsubject = relationship("StudentSubject", backref="student", order_by="StudentSubject.id")
    studentchapter = relationship("StudentChapter", backref="student", order_by="StudentChapter.id")
    representative_name = Column(String)
    representative_surname = Column(String)

    def add_commit(self):
        db.session.add(self)
        db.session.commit()

    def commit(self):
        db.session.commit(self)

    def convert_json(self):
        info = {
            "id": self.user.id,
            "name": self.user.name,
            "surname": self.user.surname,

        }
        return info


class Group(db.Model):
    __tablename__ = "group"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Integer)
    subject_id = Column(Integer, ForeignKey("subject.id"))
    platform_id = Column(Integer)
    level_id = Column(Integer, ForeignKey("subject_level.id"))
    teacher_salary = Column(Integer)
    teacher_id = Column(Integer)
    location_id = Column(Integer, ForeignKey('location.id'))

    def convert_json(self, entire=False, user=None):
        teacher = Teacher.query.filter(Teacher.id == self.teacher_id).first()
        student_subject = StudentSubject.query.filter(StudentSubject.student_id == user.student.id,
                                                      StudentSubject.subject_id == self.subject_id).first() if user and user.student else None

        info = {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "students_num": len(self.student),
            "platform_id": self.platform_id,
            "subject": {
                "id": self.subject.id,
                "name": self.subject.name,
                "finished": student_subject.finished if student_subject else None,
                "percentage": student_subject.percentage if student_subject else None
            },
            "course": self.subject_level.convert_json() if self.subject_level else {},
            "teacher": {
                "id": teacher.user_id if teacher else None,
                "name": teacher.user.name if teacher else None,
                "surname": teacher.user.surname if teacher else None,
                "salary": self.teacher_salary if teacher else None
            },
            "students": [],

        }
        if self.subject_level:
            info['course'] = {
                "id": self.subject_level.id,
                "name": self.subject_level.name,
            }
        if self.student:
            for student in self.student:
                exist_student = db.session.query(Student).join(Student.user).options(
                    contains_eager(Student.user)).filter(User.platform_id == student.user.platform_id).order_by(
                    User.id).all()
                if len(exist_student) > 1:
                    user = User.query.filter(User.id == exist_student[0].user.id).first()
                    get_student = Student.query.filter(Student.id == exist_student[0].id).first()
                    db.session.delete(user)
                    db.session.delete(get_student)
                    db.session.commit()

                student_info = {
                    "id": student.user.id,
                    "name": student.user.name,
                    'surname': student.user.surname,
                    "phone": student.user.phone,
                    "parent_phone": student.user.parent_phone,
                    "balance": student.user.balance,
                    "platform_id": student.user.platform_id,
                    "color": ["green", "yellow", "red", "navy", "black"][student.debtor] if student.debtor else 0
                }
                info['students'].append(student_info)
        return info

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


db.Table('student_group',
         db.Column('group_id', db.Integer, db.ForeignKey('group.id')),
         db.Column('student_id', db.Integer, db.ForeignKey('student.id'))
         )

db.Table('teacher_subject',
         db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.id')),
         db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'))
         )

db.Table('teacher_group',
         db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.id')),
         db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
         )


class Teacher(db.Model):
    __tablename__ = "teacher"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    groups = relationship("Group", secondary="teacher_group", backref="teacher", order_by="Group.id")
    subjects = relationship("Subject", secondary="teacher_subject", backref="teacher", order_by="Subject.id")

    def add_commit(self):
        db.session.add(self)
        db.session.commit()


class File(db.Model):
    __tablename__ = "file"
    id = Column(Integer, primary_key=True)
    url = Column(String)
    size = Column(String)
    file_name = Column(String)
    subjects = relationship("Subject", backref="file", order_by="Subject.id")
    exercise_answers = relationship("ExerciseAnswers", backref="file", order_by="ExerciseAnswers.id")
    lesson_block = relationship("LessonBlock", backref="file", order_by="LessonBlock.id")
    exercise_block = relationship("ExerciseBlockImages", backref="file", order_by="ExerciseBlockImages.id")
    users = relationship("User", backref="file", order_by="User.id")
    type_file = Column(String)

    def convert_json(self, entire=False):
        return {
            "id": self.id,
            "url": self.url,
            "size": self.size,
            "name": self.file_name,
            "type_file": self.type_file
        }

    def add(self):
        db.session.add(self)
        db.session.commit()


# from backend.basics.models import *
from backend.lessons.models import *
from backend.essay_funtions.models import *
from backend.question_answer.models import *
from backend.certificate.models import *
