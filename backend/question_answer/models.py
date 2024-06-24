from backend.models.basic_model import *
from datetime import datetime


class StudentQuestion(db.Model):
    __tablename__ = "student_question"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('student.id'))
    title = Column(String)
    question = Column(String)
    subject_id = Column(Integer, ForeignKey("subject.id"))
    date = Column(DateTime)
    img = Column(Text)
    level_id = Column(Integer, ForeignKey('subject_level.id'))
    question_answers = relationship("QuestionAnswers", lazy="select", order_by="QuestionAnswers.id")
    question_answer_comment = relationship("QuestionAnswerComment", lazy="select", order_by="QuestionAnswerComment.id")

    def convert_json(self, entire=False):
        return {
            "id": self.id,
            'title': self.title,
            "date": datetime.strptime(f'{self.date.year}-{self.date.month}-{self.date.day}', '%Y-%m-%d'),
            'student': self.student.convert_json(),
            'subject': self.subject.convert_json(),
            "img": self.file.url if self.file and self.file.url else None,
            "question": self.question,
            'answers': [answer.convert_json() for answer in self.question_answers],
            'level': None
        }


class QuestionAnswers(db.Model):
    __tablename__ = "question_answers"
    id = Column(Integer, primary_key=True)
    answer = Column(Text)
    user_id = Column(Integer, ForeignKey('user.id'))
    checked = Column(Boolean)
    date = Column(Date)
    img = Column(Text)
    question_id = Column(Integer, ForeignKey("student_question.id"))
    question_answer_comment = relationship("QuestionAnswerComment", lazy="select", order_by="QuestionAnswerComment.id")

    def convert_json(self, entire=False):
        return {
            "id": self.id,
            "date": datetime.strptime(f'{self.date.year}-{self.date.month}-{self.date.day}', '%Y-%m-%d'),
            'user': self.user.convert_json(),
            "img": self.file.url if self.file and self.file.url else None,
            'checked': self.checked,
            "answer": self.answer,
            'comments': [comment.convert_json() for comment in self.question_answer_comment],
        }


class QuestionAnswerComment(db.Model):
    __tablename__ = "question_answer_comment"
    id = Column(Integer, primary_key=True)
    answer_id = Column(Integer, ForeignKey("question_answers.id"))
    user_id = Column(Integer, ForeignKey('user.id'))
    question_id = Column(Integer, ForeignKey("student_question.id"))
    comment = Column(Text)
    date = Column(Date)

    def convert_json(self, entire=False):
        return {
            "id": self.id,
            "date": datetime.strptime(f'{self.date.year}-{self.date.month}-{self.date.day}', '%Y-%m-%d'),
            'user': self.user.convert_json(),
            'comment': self.comment,
        }
