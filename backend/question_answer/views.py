from app import api, app, cross_origin, db, request, jsonify, platform_server, or_, contains_eager

from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.basic_model import Teacher, File, Group, StudentSubject
from backend.basics.settings import edit_msg, add_file, check_file, check_img_remove, create_msg, del_msg
from backend.models.settings import User, Subject, Student, send_subject_server, iterate_models
import json
from backend.question_answer.models import QuestionAnswers, QuestionAnswerComment, StudentQuestion


@app.route(f'{api}/create_question/<int:student_id>', methods=["POST", "GET"])
def create_question(student_id):
    if request.method == "GET":
        questions = StudentQuestion.query.all()
        subjects = Subject.query.all()
        subjects_json = [subject.convert_json() for subject in subjects]
        return jsonify({'subjects': subjects_json})

    # if request.method == "POST":
