from backend.basics.settings import *
from .basic_model import *
import requests


def iterate_models(model, relationship=None, entire=False):
    list = []
    for subject in model:
        if relationship == "exercise_types":
            if not subject.exercises:
                list.append(subject.convert_json(entire=entire))
            else:
                list.append(subject.convert_json_check())
        else:
            list.append(subject.convert_json(entire=entire))
    return list


def delete_list_models(model, File, type=None):
    for subject in model:
        if type:
            if subject.audio:
                check_img_remove(subject.audio, File)
            if subject.img:
                check_img_remove(subject.img, File)
        else:
            if subject.file_id:
                check_img_remove(subject.file_id, File)
        subject.delete_commit()


def send_subject_server(type_data, platform_server, subjects):
    requests.post(f"{platform_server}/api/get_datas", headers={
        'Content-Type': 'application/json'
    }, json={
        f"{type_data}": iterate_models(subjects),
        "type": type_data
    })
