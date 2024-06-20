import requests

from app import api, app, cross_origin, db, request, jsonify, platform_server
from backend.models.settings import iterate_models
from backend.models.basic_model import Role, Teacher, User, Student, Location, Subject, SubjectLevel, Group, \
    StudentSubject
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, create_refresh_token
from pprint import pprint


@app.route(f'{api}/token', methods=["POST", "GET"])
def create_token():
    json_request = request.get_json()
    username = json_request['username'].lower()
    password = json_request['password'].lower()

    if username != "test" or password != "test":
        return {"msg": "Wrong email or password"}, 401
    access_token = create_access_token(identity=username)
    response = {"access_token": access_token}
    return response


@app.route(f"{api}/refresh/<token>", methods=["POST"])
@cross_origin()
@jwt_required(refresh=True)
def refresh(token):
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    user = User.query.filter_by(user_id=identity).first()
    response = requests.post(f"{platform_server}/api/refresh", headers={
        "Authorization": "Bearer " + token,
        'Content-Type': 'application/json'
    })
    info = {
        "info": user.convert_json(),
        "access_token": access_token,
        "refresh_token": create_refresh_token(identity=user.user_id),
        "old_access_token": response.json()['access_token'],
        "platform_refresh_token": response.json()['refresh_token'],
        "img": response.json()['profile_photo']

    }
    info['info'].update(response.json()['teacher_info'] if 'teacher_info' in response.json() else {})

    return jsonify({
        "data": info
    })


@app.route(f'{api}/send_user/<token>')
@cross_origin()
def send_user(token):
    response = requests.get(f"{platform_server}/api/get_user", headers={
        "Authorization": "Bearer " + token,
        'Content-Type': 'application/json'
    })
    if 'data' not in response.json():
        return jsonify({
            "msg": "Not logged in"
        })
    subject_list = response.json()['subject_list']
    # users = response.json()['users']
    # for user in users:
    #     user_get = User.query.filter(User.user_id == user['user_id']).first()
    #     if user_get:
    #         user_get.username = user['username']
    #         db.session.commit()

    for sub in subject_list:
        get_subject = Subject.query.filter(Subject.name == sub['name']).first()
        if not get_subject:
            get_subject = Subject(name=sub['name'])
            get_subject.add_commit()

    item = response.json()['data']
    location_id = item['location']['id']
    location_name = item['location']['name']
    role_id = item["role"]['id']
    role_type = item['role']['name']
    role_token = item['role']['role']
    role = Role.query.filter(Role.platform_id == role_id).first()
    if not role:
        role = Role(platform_id=role_id, type=role_type, role=role_token)
        role.add_commit()
    location = Location.query.filter(Location.platform_id == location_id).first()
    if not location:
        location = Location(name=location_name, platform_id=location_id)
        location.add_commit()

    print(item['username'])
    user = User.query.filter(User.username == item['username']).first()
    if not user:

        user = User(username=item['username'], name=item['name'], surname=item['surname'], balance=item['balance'],
                    password=item['password'], platform_id=item['id'], location_id=location.id, role_id=role.id,
                    age=item['age'], father_name=item['father_name'], born_day=item['born_day'],
                    born_month=item['born_month'], born_year=item['born_year'], user_id=item['user_id'])
        user.add_commit()
        for phone in item['phone']:
            if phone['personal']:
                user.phone = phone['phone']
            else:
                user.parent_phone = phone['phone']
            db.session.commit()
    else:
        User.query.filter(User.username == item['username']).update({
            "location_id": location.id,
            "role_id": role.id,
            "balance": item['balance'],
        })
        for phone in item['phone']:
            if phone['personal']:
                user.phone = phone['phone']
            else:
                user.parent_phone = phone['phone']
            db.session.commit()
        user.born_year = item['born_year']
        user.born_month = item['born_month']
        user.born_day = item['born_day']
        user.father_name = item['father_name']
        user.age = item['age']
        user.user_id = item['user_id']
        db.session.commit()
    if item['student']:

        student = Student.query.filter(Student.user_id == user.id).first()
        if not student:
            student = Student(user_id=user.id, debtor=item['student']['debtor'],
                              representative_name=item['student']['representative_name'],
                              representative_surname=item['student']['representative_surname'])
            student.add_commit()
        else:
            Student.query.filter(Student.user_id == user.id).update({
                "debtor": item['student']['debtor'],
                "representative_name": item['student']['representative_name'],
                "representative_surname": item['student']['representative_surname']
            })
            db.session.commit()
        for gr in item['student']['group']:
            group = check_group_info(gr)

            if group not in student.groups:
                student.groups.append(group)
                db.session.commit()
            subject = Subject.query.filter(Subject.id == group.subject_id).first()
            student_subject = StudentSubject.query.filter(StudentSubject.subject_id == subject.id,
                                                          StudentSubject.student_id == student.id).first()
            if not student_subject:
                student_subject = StudentSubject(subject_id=subject.id, student_id=student.id)
                student_subject.add_commit()
    if item['teacher']:
        teacher = Teacher.query.filter(Teacher.user_id == user.id).first()
        if not teacher:
            teacher = Teacher(user_id=user.id)
            teacher.add_commit()
        group_list = []
        for gr in item['teacher']['group']:
            group_list.append(gr['id'])
            group = check_group_info(gr)
            print('group_teacher', group.teacher_id)
            if group not in teacher.groups:
                teacher.groups.append(group)
                db.session.commit()
            group.teacher_id = teacher.id
            subject = Subject.query.filter(Subject.id == group.subject_id).first()
            if subject not in teacher.subjects:
                teacher.subjects.append(subject)
            db.session.commit()
        # for gr in teacher.groups:
        #     if gr.platform_id not in group_list:
        #         teacher.groups.remove(gr)
        #         db.session.commit()

    access_token = create_access_token(identity=user.user_id)
    return jsonify({
        "data": {
            "info": user.convert_json(),
            "access_token": access_token,
            "refresh_token": create_refresh_token(identity=user.user_id)
        }
    })


@app.route('/send_datas')
@jwt_required()
def send_datas():
    subjects = Subject.query.order_by(Subject.id).order_by(Subject.id).all()
    return jsonify({
        "data": iterate_models(subjects, entire=True)
    })


def check_group_info(gr):
    group = Group.query.filter(Group.platform_id == gr['id']).first()
    # pprint(gr)
    # if 'course' in gr:
    #     level = SubjectLevel.query.filter(SubjectLevel.name == gr['course']['name']).first()
    #     if not level:
    #         level = SubjectLevel(name=gr['course']['name'])
    #         level.add_commit()
    #     level_id = level.id
    # else:
    #     level_id = None
    if not group:
        location = Location.query.filter(Location.platform_id == gr['location']['id']).first()
        subject_name = gr['subjects']['name']
        subject = Subject.query.filter(Subject.name == subject_name).first()
        group = Group(platform_id=gr['id'], name=gr['name'], price=gr['price'],
                      teacher_salary=gr['teacher_salary'], location_id=location.id,
                      subject_id=subject.id,
                      # level_id=level_id

                      )
        group.add_commit()

    else:
        Group.query.filter(Group.platform_id == gr['id']).update({
            "teacher_salary": gr['teacher_salary'],
            "price": gr['price'], "name": gr['name']
        })
        db.session.commit()
    return group


@app.errorhandler(404)
def not_found(e):
    return app.send_static_file('index.html')


@app.route('/', methods=['POST', 'GET'])
def index():
    return app.send_static_file("index.html")


@app.route(f'{api}/update_user_info', methods=['POST'])
def update_user_info():
    user_get = request.get_json()['user']
    User.query.filter(User.platform_id == user_get['id']).update({
        "username": user_get['username']
    })
    db.session.commit()
    return jsonify({
        "msg": "hello"
    })
