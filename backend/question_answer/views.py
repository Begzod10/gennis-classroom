from app import api, app, cross_origin, db, request, jsonify, platform_server, or_, contains_eager

from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.basic_model import Teacher, File, Group, StudentSubject
from backend.basics.settings import edit_msg, add_file, check_file, check_img_remove, create_msg, del_msg
from backend.models.settings import User, Subject, Student, send_subject_server, iterate_models
import json
from backend.question_answer.models import QuestionAnswers, QuestionAnswerComment, StudentQuestion
from datetime import datetime
from backend.basics.settings import save_img


@app.route(f'{api}/create_question', methods=["POST", "GET"])
def create_question():
    if request.method == "GET":
        questions = StudentQuestion.query.all()
        questions_json = [question.convert_json() for question in questions]
        subjects = Subject.query.all()
        subjects_json = [subject.convert_json() for subject in subjects]
        return jsonify({'subjects': subjects_json, 'questions': questions_json})

    if request.method == "POST":
        today = datetime.today()
        date = datetime.strptime(f'{today.year}-{today.month}-{today.day}', "%Y-%m-%d")
        data = request.get_json()
        level_id = data.get('level_id')
        subject_id = data.get('subject_id')
        student_id = data.get('student_id')
        question = data.get('question')
        photo = request.files['file']
        img_info = save_img(photo, app)
        title = data.get('title')
        add_question = StudentQuestion(title=title, student_id=student_id, question=question, level_id=level_id,
                                       subject_id=subject_id, date=date, img=img_info['photo_url'])
        db.session.add(add_question)
        db.session.commit()
        return jsonify({'question': add_question.convert_json(), 'msg': "savol muvaffaqqiyatli qo'shildi"})


@app.route(f'{api}/add_answer/<int:question_id>', methods=["POST", "GET"])
def add_answer(question_id):
    if request.method == "POST":
        today = datetime.today()
        date = datetime.strptime(f'{today.year}-{today.month}-{today.day}', "%Y-%m-%d")
        data = request.get_json()
        user_id = data.get('user_id')
        answer = data.get('answer')
        photo = request.files['file']
        img_info = save_img(photo, app)
        add_answer = QuestionAnswers(question_id=question_id,
                                     answer=answer, date=date, img=img_info['photo_url'], user_id=user_id)
        db.session.add(add_answer)
        db.session.commit()
        question = StudentQuestion.query.filter_by(id=question_id).first()
        return jsonify({'msg': "javob muvaffaqqiyatli qo'shildi", 'question': question.convert_json()})


@app.route(f'{api}/add_comment/<int:question_id>/<int:answer_id>', methods=["POST", "GET"])
def add_comment(question_id, answer_id):
    if request.method == "POST":
        today = datetime.today()
        date = datetime.strptime(f'{today.year}-{today.month}-{today.day}', "%Y-%m-%d")
        data = request.get_json()
        user_id = data.get('user_id')
        comment = data.get('comment')
        add_comment = QuestionAnswerComment(question_id=question_id,
                                            comment=comment, date=date, user_id=user_id, answer_id=answer_id)
        db.session.add(add_comment)
        db.session.commit()
        question = StudentQuestion.query.filter_by(id=question_id).first()
        return jsonify({'msg': "comment muvaffaqqiyatli qo'shildi", 'question': question.convert_json()})


@app.route(f'{api}/check_answer/<int:answer_id>/<int:question_id>', methods=["POST", "GET"])
def check_answer(answer_id, question_id):
    if request.method == "POST":
        data = request.get_json()
        user_id = data.get('user_id')
        check = data.get('check')
        question = StudentQuestion.query.filter_by(id=question_id).first()
        if question.student.user_id == user_id:
            QuestionAnswers.query.filter_by(id=answer_id).update({
                'check': True if check == True else False
            })
            db.session.commit()
            question = StudentQuestion.query.filter_by(id=question_id).first()
            return jsonify({'question': question.convert_json()})
        else:
            return jsonify({'msg': "javobga check qo'ya olmaysiz"})
