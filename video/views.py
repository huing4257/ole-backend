import os
import re
from wsgiref.util import FileWrapper

import filetype
from django.http import HttpRequest, StreamingHttpResponse

from utils.utils_check import CheckLogin
from utils.utils_request import request_success, BAD_METHOD, request_failed
from video.models import Video


# Create your views here.

def upload_handler(video, filename=None):
    vid = Video(video_file=video)
    vid.filename = filename
    vid.save()
    return {"url": vid.video_file.name}


@CheckLogin
def upload(req: HttpRequest, user):
    if req.method == "POST":
        return request_success(upload_handler(req.FILES['video']))
    else:
        return BAD_METHOD


def video_iterator(video, chunk_size=8192, offset=0, length=None):
    video = video.video_file.open(mode='rb')
    video.seek(offset, os.SEEK_SET)
    remaining = length
    while True:
        bytes_length = chunk_size if remaining is None else min(remaining, chunk_size)
        data = video.read(bytes_length)
        if not data:
            break
        if remaining:
            remaining -= len(data)
        yield data
    video.close()


def get_vid(req: HttpRequest, vid_url):
    range_header = req.META.get('HTTP_RANGE', '').strip()
    range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)
    range_match = range_re.match(range_header)
    vid = Video.objects.filter(video_file=vid_url).first()
    if (not vid) or (not os.path.exists(vid.video_file.path)):
        return request_failed(18, "video not found", 404)
    vid_content = vid.video_file.open(mode='rb')
    vid_type = filetype.guess_mime(vid_content)
    vid_content.close()
    size = vid.video_file.size
    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = first_byte + 1024 * 1024 * 10
        if last_byte >= size:
            last_byte = size - 1
        length = last_byte - first_byte + 1
        resp = StreamingHttpResponse(video_iterator(vid, offset=first_byte, length=length),
                                     content_type=vid_type, status=206)
        resp['Content-Length'] = str(length)
        resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
    else:
        resp = StreamingHttpResponse(FileWrapper(vid.video_file.open(mode="rb")), content_type=vid_type)
        resp['Content-Length'] = str(size)
    resp['Accept-Ranges'] = 'bytes'
    return resp


def delete_vid(req, img_url):
    vid = Video.objects.filter(video_file=img_url).first()
    if not vid:
        return request_failed(18, "video not found", 404)
    if os.path.exists(vid.video_file.path):
        vid.video_file.delete()
    vid.delete()
    return request_success()


@CheckLogin
def video_handler(req: HttpRequest, user, video_url):
    if req.method == "GET":
        return get_vid(req, video_url)
    elif req.method == "DELETE":
        return delete_vid(req, video_url)
    else:
        return BAD_METHOD
