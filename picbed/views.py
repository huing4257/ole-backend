import filetype
from django.http import HttpRequest, HttpResponse
from picbed.models import Image
from utils.utils_request import request_success


# Create your views here.

def upload(req: HttpRequest):
    img = Image(img_file=req.FILES['file'])
    img.save()
    return request_success({"file": img.img_file.name})


def get_img(req: HttpRequest, img_url):
    img = Image.objects.filter(img_file=img_url).first()
    img_content = img.img_file.open(mode='rb').read()
    img_type = filetype.guess_mime(img_content)
    return HttpResponse(img_content, content_type=img_type)
