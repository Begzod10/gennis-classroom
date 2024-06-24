import os
from werkzeug.utils import secure_filename

# from app import *

# from .views import *

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def check_file(filename):
    value = '.' in filename
    type_file = filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    return value and type_file


def check_img_remove(img, File):
    img = File.query.filter(File.id == img).first()
    exist = False
    if img:
        if img.subjects or img.exercise_answers or img.lesson_block or img.exercise_block or img.users or img.file_audio or img.file_img:
            exist = True
        if not exist:
            if os.path.isfile("frontend/build" + img.url):
                os.remove("frontend/build" + img.url)


def save_img(photo, app, type_file=None):
    symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")

    tr = {ord(a): ord(b) for a, b in zip(*symbols)}

    text = f'{photo.filename}'
    file_name = text.translate(tr)
    photo_file = secure_filename(file_name)
    if type_file == "file":
        photo_url = file_url() + "/" + photo_file
        app.config['UPLOAD_FOLDER'] = file_folder()
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_file))
        return (photo_url, file_name)
    elif type_file == "audio":
        photo_url = audio_url() + "/" + photo_file
        app.config['UPLOAD_FOLDER'] = audio_folder()
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_file))
        return (photo_url, file_name)
    if not type_file:
        photo_url = img_url() + "/" + photo_file
        app.config['UPLOAD_FOLDER'] = img_folder()
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_file))
        return (photo_url, file_name)
    photo_url = img_url() + "/" + photo_file
    app.config['UPLOAD_FOLDER'] = img_folder()
    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_file))
    return (photo_url, file_name)


def add_file(photo, type_file, app, File):
    photo_url, file_name = save_img(photo, app, type_file=type_file)

    mb_size = str(define_size(f'frontend/build/{photo_url}'))
    print(file_name)
    img_add = File.query.filter(File.url == photo_url, File.size == mb_size, File.type_file == type_file,
                                File.file_name == file_name).first()
    if not img_add:
        img_add = File(url=photo_url, size=mb_size, type_file=type_file, file_name=file_name)
        img_add.add()
    return img_add.id


def define_size(url):
    byte_size = os.path.getsize(url)
    return byte_size / (1024 * 1024)


def img_folder():
    return 'frontend/build/static/img'


def img_url():
    return 'static/img'


def file_url():
    return 'static/files'


def file_folder():
    return 'frontend/build/static/files'


def audio_folder():
    return 'frontend/build/static/audio'


def audio_url():
    return "static/audio"


def create_msg(item, status, data=None):
    if status:
        msg = f"{item} muvaffaqiyatli yaratildi",
        success = "success"
    else:
        msg = f"{item} muvaffaqiyatsiz yaratildi",
        success = "danger"

    return {
        "msg": msg,
        "data": data,
        "status": success
    }


def edit_msg(item, status, data=None):
    if status:
        msg = f"{item} muvaffaqiyatli o'zgaritirildi",
        success = "success"
    else:
        msg = f"{item} muvaffaqiyatsiz o'zgartirildi",
        success = "danger"

    return {
        "msg": msg,
        "data": data,
        "status": success
    }


def del_msg(item, status, data=None):
    if status:
        success = "success"
        msg = f"{item} muvaffaqiyatli o'chirildi"
    else:
        msg = f"{item} o'chirilmadi"
        success = "danger"
    return {
        "msg": msg,
        "status": success,
        "data": data
    }
