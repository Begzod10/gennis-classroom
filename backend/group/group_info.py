from app import app, api, cross_origin, db, contains_eager, request, or_, jsonify, platform_server
from backend.models.basic_model import Student, StudentLevel, Teacher, Group, SubjectLevel, User, StudentSubject, \
    Location, Role, Subject, Chapter, StudentChapter, StudentLesson
from flask_jwt_extended import get_jwt_identity, jwt_required
from backend.models.settings import iterate_models
from pprint import pprint
import requests
from backend.basics.views import check_group_info
import uuid
from sqlalchemy.exc import IntegrityError, PendingRollbackError


# from backend.basics.settings import


@app.route(f'{api}/get_groups')
@cross_origin()
@jwt_required()
def get_groups():
    identity = get_jwt_identity()
    user = User.query.filter_by(user_id=identity).first()
    student = Student.query.filter(Student.user_id == user.id).first()
    teacher = Teacher.query.filter(Teacher.user_id == user.id).first()

    # users = User.query.filter(User.teacher != None).order_by(User.id).all()
    # for item in users:
    #     print(item.username)
    #     item.student = None
    #     db.session.commit()
    # students = Student.query.filter(Student.user_id == None).all()
    # for st in students:
    #     db.session.delete(st)
    #     db.session.commit()
    # print(len(students))
    # print(user.student)
    # print(user.teacher)
    if student:
        groups = db.session.query(Group).join(Group.student).options(contains_eager(Group.student)).filter(
            Student.id == student.id).order_by(Group.platform_id).all()
        for group in groups:
            student_subject = StudentSubject.query.filter(StudentSubject.subject_id == group.subject_id,
                                                          StudentSubject.student_id == student.id).first()
            if not student_subject:
                student_subject = StudentSubject(subject_id=group.subject_id,
                                                 student_id=student.id)
                db.session.add(student_subject)
                db.session.commit()
        groups = db.session.query(Group).join(Group.student).options(contains_eager(Group.student)).filter(
            Student.id == student.id).order_by(Group.platform_id).all()

    else:
        groups = db.session.query(Group).join(Group.teacher).options(contains_eager(Group.teacher)).filter(
            Teacher.id == teacher.id).order_by(Group.platform_id).all()

    return iterate_models(groups)


@app.route(f'{api}/group_observer/<group_id>')
@jwt_required()
def group_observer(group_id):
    group = Group.query.filter(Group.platform_id == group_id).first()
    return jsonify({
        "data": group.convert_json()
    })


@app.route(f'{api}/group_profile2/<int:group_id>/', defaults={"token": None})
@app.route(f'{api}/group_profile2/<int:group_id>/<token>')
@jwt_required()
def group_profile(group_id, token):
    identity = get_jwt_identity()
    user = User.query.filter_by(user_id=identity).first()
    student = Student.query.filter(Student.user_id == user.id).first()
    group = Group.query.filter(Group.id == group_id).first()
    if token:
        requests.post(f"{platform_server}/api/update_group_datas", headers={
            "Authorization": "Bearer " + token,
            'Content-Type': 'application/json'
        }, json={
            "group": group.convert_json()
        })
        response = requests.get(f"{platform_server}/api/get_group_datas/{group.platform_id}", headers={
            "Authorization": "Bearer " + token,
            'Content-Type': 'application/json'
        })
        if 'users' not in response.json():
            return jsonify({
                "msg": "Not logged in"
            })
        users = response.json()['users']
        for item in users:
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
            exist_user = User.query.filter(User.username == item['username']).first()
            if not exist_user:
                exist_user = User(username=item['username'], name=item['name'], surname=item['surname'],
                                  balance=item['balance'],
                                  password=item['password'], platform_id=item['id'], location_id=location.id,
                                  role_id=role.id,
                                  age=item['age'], father_name=item['father_name'], born_day=item['born_day'],
                                  born_month=item['born_month'], born_year=item['born_year'],
                                  user_id=item['user_id'])
                exist_user.add_commit()
                for phone in item['phone']:
                    if phone['personal']:
                        exist_user.phone = phone['phone']
                    else:
                        exist_user.parent_phone = phone['phone']
                    db.session.commit()
            else:
                User.query.filter(User.username == item['username']).update({
                    "location_id": location.id,
                    "role_id": role.id,
                    "balance": item['balance'],
                })
                for phone in item['phone']:
                    if phone['personal']:
                        exist_user.phone = phone['phone']
                    else:
                        exist_user.parent_phone = phone['phone']
                    db.session.commit()
                exist_user.born_year = item['born_year']
                exist_user.born_month = item['born_month']
                exist_user.born_day = item['born_day']
                exist_user.father_name = item['father_name']
                exist_user.age = item['age']
                exist_user.user_id = item['user_id']
                db.session.commit()
            student = Student.query.filter(Student.user_id == exist_user.id).first()
            if not student:
                student = Student(user_id=exist_user.id, debtor=item['student']['debtor'],
                                  representative_name=item['student']['representative_name'],
                                  representative_surname=item['student']['representative_surname'])
                student.add_commit()
            else:
                Student.query.filter(Student.user_id == exist_user.id).update({
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
        users_list = []
        for user in users:
            users_list.append(user['id'])
        exist_students = db.session.query(Student).join(Student.user).options(contains_eager(Student.user)).filter(
            ~User.platform_id.in_(users_list)).join(Student.groups).filter(Group.id == group_id).all()
        for st in exist_students:
            if group in st.groups:
                st.groups.remove(group)
                db.session.commit()

    student_level = StudentLevel.query.filter(StudentLevel.group_id == group_id).all()
    levels = SubjectLevel.query.filter(SubjectLevel.id.in_([level.level_id for level in student_level])).all()
    students = Student.query.join(Student.groups).filter(Group.id == group_id).all()
    if len(students) > len(student_level):
        for level in levels:

            for student in students:
                exist_chapter = StudentLevel.query.filter(StudentLevel.group_id == group_id,
                                                          StudentLevel.student_id == student.id,
                                                          StudentLevel.level_id == level.id,
                                                          StudentLevel.subject_id == level.subject_id,
                                                          ).first()
                if not exist_chapter:
                    exist = StudentLevel(student_id=student.id, level_id=level.id, group_id=group_id,
                                         subject_id=level.subject_id, disabled=True)
                    exist.add_commit()
            chapters = Chapter.query.filter(Chapter.level_id == level.id).order_by(Chapter.order).all()
            for chapter in chapters:
                exist_chapter = StudentChapter.query.filter(StudentChapter.chapter_id == chapter.id,
                                                            StudentChapter.student_id == student.id,
                                                            StudentChapter.level_id == chapter.level_id).first()
                if not exist_chapter:
                    exist_chapter = StudentChapter(level_id=chapter.level_id, chapter_id=chapter.id,
                                                   student_id=student.id, order=chapter.order)
                    exist_chapter.add()
                else:
                    exist_chapter.order = chapter.order
                    db.session.commit()
                for lesson in chapter.lesson:
                    if not lesson.disabled:
                        student_lesson = StudentLesson.query.filter(StudentLesson.lesson_id == lesson.id,
                                                                    StudentLesson.student_id == student.id,
                                                                    StudentLesson.level_id == level.id,
                                                                    StudentLesson.self_chapter_id == exist_chapter.id,
                                                                    StudentLesson.chapter_id == chapter.id).first()
                        if not student_lesson:
                            student_lesson = StudentLesson(lesson_id=lesson.id, student_id=student.id,
                                                           level_id=level.id, self_chapter_id=exist_chapter.id,
                                                           order=lesson.order, chapter_id=chapter.id)
                            student_lesson.add_commit()
    levels = SubjectLevel.query.filter(SubjectLevel.subject_id == group.subject_id).filter(
        or_(SubjectLevel.disabled == False, SubjectLevel.disabled == None)).order_by(SubjectLevel.id).all()

    group = Group.query.filter(Group.id == group_id).first()
    if student:
        subject_level = db.session.query(StudentLevel).join(StudentLevel.subject_level).options(
            contains_eager(StudentLevel.subject_level)).filter(StudentLevel.student_id == student.id,
                                                               StudentLevel.group_id == group_id).order_by(
            SubjectLevel.id).all()

    else:

        subject_level = SubjectLevel.query.filter(SubjectLevel.subject_id == group.subject_id).order_by(
            SubjectLevel.id).all()
    return jsonify({
        "data": group.convert_json(),
        "subject_levels": iterate_models(levels),
        "curriculum": iterate_models(subject_level)
    })


@app.route(f'{api}/set_observer/<int:user_id>')
def set_observer(user_id):
    user = User.query.filter(User.platform_id == user_id).first()

    user.observer = not user.observer
    db.session.commit()

    action = "given" if user.observer else "taken"
    response_message = f"Permission was {action}"
    return jsonify({
        "msg": response_message,
        "success": True
    })


@app.route(f'{api}/update_student_balance', methods=['POST'])
def update_student_balance():
    platform_id = request.get_json()['platform_id']
    balance = request.get_json()['balance']
    teacher_id = request.get_json()['teacher_id']
    salary = request.get_json()['salary']
    debtor = request.get_json()['debtor']
    User.query.filter(User.platform_id == teacher_id).update({
        "balance": salary
    })
    User.query.filter(User.platform_id == platform_id).update({
        "balance": balance
    })
    db.session.commit()
    user = User.query.filter(User.platform_id == platform_id).first()
    Student.query.filter(Student.user_id == user.id).update({
        "debtor": debtor
    })
    db.session.commit()
    return jsonify({
        "msg": "Balance o'zgartirildi"
    })


@app.route(f'{api}/check_level/<group_id>/<level_id>', methods=['POST', 'GET'])
def check_level(group_id, level_id):
    subject_level = SubjectLevel.query.filter(SubjectLevel.id == level_id).first()
    if request.method == "POST":
        student_list = request.get_json()['users']
        for st in student_list:
            student = Student.query.filter(Student.user_id == st['id']).first()
            exist = StudentLevel.query.filter(StudentLevel.level_id == subject_level.id,
                                              StudentLevel.student_id == student.id,
                                              StudentLevel.group_id == group_id,
                                              StudentLevel.subject_id == subject_level.subject_id).first()
            disabled = False if st['level'] else True
            if not exist:
                exist = StudentLevel(student_id=student.id, level_id=subject_level.id, group_id=group_id,
                                     subject_id=subject_level.subject_id, disabled=disabled)
                exist.add_commit()
            else:
                exist.disabled = False if st['level'] else True
                db.session.commit()

        return jsonify({
            "msg": f"O'zgartirildi",
            "status": 'success'
        })
    students = db.session.query(Student).join(Student.groups).options(contains_eager(Student.groups)).filter(
        Group.id == group_id).order_by(Student.id).all()

    student_list = []
    for student in students:
        exist_level = False
        exist = StudentLevel.query.filter(StudentLevel.level_id == subject_level.id,
                                          StudentLevel.student_id == student.id,
                                          StudentLevel.group_id == group_id,
                                          StudentLevel.disabled != True).first()
        if exist:
            exist_level = True
        info = student.convert_json()
        info['level'] = exist_level
        student_list.append(info)
    return jsonify({
        "students": student_list
    })
