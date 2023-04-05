import filetype
from django.http import HttpRequest, HttpResponse
from picbed.models import Image
from utils.utils_request import request_success, BAD_METHOD, request_failed


# Create your views here.

def upload(req: HttpRequest):
    img = Image(img_file=req.FILES['img'])
    img.save()
    return request_success({"url": img.img_file.name})


def get_img(req: HttpRequest, img_url):
    img = Image.objects.filter(img_file=img_url).first()
    if not img:
        return request_failed(18, "picture not found", 404)
    img_content = img.img_file.open(mode='rb').read()
    img.img_file.close()
    img_type = filetype.guess_mime(img_content)
    return HttpResponse(img_content, content_type=img_type)


def delete_img(req, img_url):
    img = Image.objects.filter(img_file=img_url).first()
    if not img:
        return request_failed(18, "picture not found", 404)
    img.img_file.delete()
    img.delete()
    return request_success()


def img_handler(req: HttpRequest, img_url):
    img_url = "picbed/" + img_url
    if req.method == "GET":
        return get_img(req, img_url)
    elif req.method == "DELETE":
        return delete_img(req, img_url)
    else:
        return BAD_METHOD
