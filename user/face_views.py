import base64
import json
import re
# from io import BytesIO

# from PIL import Image as PIL_Image
import face_recognition
from django.core.files.uploadedfile import SimpleUploadedFile

from user.models import User
from user.views import login_success
from utils.utils_check import CheckLogin
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import CheckRequire, require


def face_base64_to_ndarray(image_base64):
    image_base64 = re.sub('^data:image/.+;base64,', '', image_base64)
    image_byte = base64.b64decode(image_base64)
    image_data = SimpleUploadedFile("face.jpg", image_byte, content_type='image/jpeg')
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
        image_encoding = face_recognition.face_encodings(image)[0]
        for user_1 in User.objects.all():
            if user_1.face_base64 is None:
                continue
            user_face_base64 = user_1.face_base64
            user_face = face_base64_to_ndarray(user_face_base64)
            user_face_encoding = face_recognition.face_encodings(user_face)[0]

            results = face_recognition.compare_faces([image_encoding], user_face_encoding, tolerance=0.4)
            if results[0]:
                return request_failed(63, "face registered", 401)
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
        face_locations = face_recognition.face_locations(image)
        if len(face_locations) != 1:
            return request_failed(60, "face unrecognized")
        image_encoding = face_recognition.face_encodings(image)[0]
        for user in User.objects.all():
            if user.face_base64 is None:
                continue
            user_face_base64 = user.face_base64
            user_face = face_base64_to_ndarray(user_face_base64)
            user_face_encoding = face_recognition.face_encodings(user_face)[0]

            results = face_recognition.compare_faces([image_encoding], user_face_encoding, tolerance=0.4)
            if results[0]:
                return login_success(user)
        return request_failed(61, "face unmatched")
    else:
        return BAD_METHOD
