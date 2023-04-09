import os.path
import filetype
from django.http import HttpRequest, HttpResponse
from picbed.models import Image
from user.models import User
from utils.utils_request import request_success, BAD_METHOD, request_failed
from utils.utils_check import CheckLogin


# Create your views here.

def upload_handler(image):
    """
    用于处理图片上传
    返回值为 该图片在数据库中的唯一标识符
    前端使用时需要 api/{url}
    """
    img = Image(img_file=image)
    img.save()
    return {"url": img.img_file.name}


@CheckLogin
def upload(req: HttpRequest,user:User):
    return request_success(upload_handler(req.FILES['img']))


def get_img(req: HttpRequest, img_url):
    img = Image.objects.filter(img_file=img_url).first()
    if (not img) or (not os.path.exists(img.img_file.path)):
        return request_failed(18, "picture not found", 404)
    img_content = img.img_file.open(mode='rb').read()
    img.img_file.close()
    img_type = filetype.guess_mime(img_content)
    return HttpResponse(img_content, content_type=img_type)


def delete_img(req, img_url):
    img = Image.objects.filter(img_file=img_url).first()
    if not img:
        return request_failed(18, "picture not found", 404)
    if os.path.exists(img.img_file.path):
        img.img_file.delete()
    img.delete()
    return request_success()


@CheckLogin
def img_handler(req: HttpRequest,user:User, img_url):
    """
    处理图片的获取和删除
    """
    img_url = "picbed/" + img_url
    if req.method == "GET":
        return get_img(req, img_url)
    elif req.method == "DELETE":
        return delete_img(req, img_url)
    else:
        return BAD_METHOD
