import base64
import json
from io import BytesIO

import face_recognition

from user.models import User
from user.views import login_success
from utils.utils_check import CheckLogin
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import CheckRequire, require


def face_base64_to_ndarray(image_base64):
    image_byte = base64.b64decode(image_base64)
    image_data = BytesIO(image_byte)
    image = face_recognition.load_image_file(image_data)
    return image


@CheckLogin
@CheckRequire
def face_reco(req, user: User):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        image_base64 = require(body, "image", "string", err_msg="Missing or error type of [image]")
        image = face_base64_to_ndarray(image_base64)
        face_locations = face_recognition.face_locations(image)
        if len(face_locations) != 1:
            return request_failed(60, "face unrecognized")
        user.face_base64 = image_base64
        user.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckRequire
def face_reco_login(req):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        image_base64 = require(body, "image", "string", err_msg="Missing or error type of [image]")
        image = face_base64_to_ndarray(image_base64)
        image_encoding = face_recognition.face_encodings(image)[0]
        face_locations = face_recognition.face_locations(image)
        if len(face_locations) != 1:
            return request_failed(60, "face unrecognized")
        for user in User.objects.all():
            user_face_base64 = user.face_base64
            user_face = face_base64_to_ndarray(user_face_base64)
            user_face_encoding = face_recognition.face_encodings(user_face)[0]

            results = face_recognition.compare_faces([image_encoding], user_face_encoding)
            if results[0]:
                return login_success(user)
        return request_success()
    else:
        return BAD_METHOD
