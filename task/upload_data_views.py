import time
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest

from picbed.models import Image
from task.models import TextData
from user.models import User
from utils.utils_check import CheckLogin, CheckUser
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import CheckRequire, require
from video.models import Video


def create_text_data(data, filename):
    text_data = TextData(data=data, filename=filename)
    text_data.save()
    return {
        "filename": filename,
        "tag": str(text_data.id),
    }


def create_image_data(data, filename):
    data_file = SimpleUploadedFile(filename, data, content_type='image/jpeg')
    img_data = Image(img_file=data_file, filename=filename)
    img_data.save()
    return {
        "filename": filename,
        "tag": str(f"picbed/{img_data.img_file.name}"),
    }


def create_video_data(data, filename):
    data_file = SimpleUploadedFile(filename, data, content_type='video/mp4')
    vid_data = Video(video_file=data_file, filename=filename)
    vid_data.save()
    return {
        "filename": filename,
        "tag": str(f"video/{vid_data.video_file.name}"),
    }


def create_audio_data(data, filename):
    data_file = SimpleUploadedFile(filename, data, content_type='audio/mpeg')
    aud_data = Video(video_file=data_file, filename=filename)
    aud_data.save()
    return {
        "filename": filename,
        "tag": str(f"video/{aud_data.video_file.name}"),
    }


@CheckLogin
@CheckUser
@CheckRequire
def upload_data(req: HttpRequest, user: User):
    # 上传一个压缩包，根目录下有 x.txt/x.jpg x为连续自然数字
    if req.method == "POST":
        data_type = require(req.GET, "data_type")
        zfile = require(req.FILES, 'file', 'file')
        zfile_size = len(zfile) / 1_000_000
        print(zfile_size)
        if user.membership_level == 0:
            time.sleep(zfile_size * 10)
        elif user.membership_level == 1:
            time.sleep(zfile_size * 7)
        elif user.membership_level == 2:
            time.sleep(zfile_size * 3)
        zfile = zipfile.ZipFile(zfile)
        if data_type == 'text':
            zfile.infolist()
            text_datas = []
            flag = True
            i = 1
            for i in range(1, 1 + len(zfile.namelist())):
                filename = f"{i}.txt"
                if filename not in zfile.namelist():
                    flag = False
                    break
                data = zfile.read(f"{i}.txt").decode('utf-8')
                text_datas.append(create_text_data(data, filename))
            if not flag:
                return_data = {
                    "files": text_datas,
                    "upload_num": len(zfile.namelist()),
                    "legal_num": i - 1,
                }
                return request_failed(20, "file sequence interrupt", 200, data=return_data)
            return request_success(text_datas)
        elif data_type == 'image':
            img_datas = []
            flag = True
            i = 1
            for i in range(1, 1 + len(zfile.namelist())):
                filename = f"{i}.jpg"
                if filename not in zfile.namelist():
                    flag = False
                    break
                data = zfile.read(f"{i}.jpg")
                img_datas.append(create_image_data(data, filename))
            if not flag:
                return_data = {
                    "files": img_datas,
                    "upload_num": len(zfile.namelist()),
                    "legal_num": i - 1,
                }
                return request_failed(20, "file sequence interrupt", 200, data=return_data)
            return request_success(img_datas)
        elif data_type == 'video':
            vid_datas = []
            flag = True
            i = 1
            for i in range(1, 1 + len(zfile.namelist())):
                filename = f"{i}.mp4"
                if filename not in zfile.namelist():
                    flag = False
                    break
                data = zfile.read(f"{i}.mp4")
                vid_datas.append(create_video_data(data, filename))
            if not flag:
                return_data = {
                    "files": vid_datas,
                    "upload_num": len(zfile.namelist()),
                    "legal_num": i - 1,
                }
                return request_failed(20, "file sequence interrupt", 200, data=return_data)
            return request_success(vid_datas)
        elif data_type == 'audio':
            aud_datas = []
            flag = True
            i = 1
            for i in range(1, 1 + len(zfile.namelist())):
                filename = f"{i}.mp3"
                if filename not in zfile.namelist():
                    flag = False
                    break
                data = zfile.read(f"{i}.mp3")
                aud_datas.append(create_audio_data(data, filename))
            if not flag:
                return_data = {
                    "files": aud_datas,
                    "upload_num": len(zfile.namelist()),
                    "legal_num": i - 1,
                }
                return request_failed(20, "file sequence interrupt", 200, data=return_data)
            return request_success(aud_datas)
        elif data_type == 'verify':
            audit_datas = []
            flag = True
            i = 1
            for i in range(1, 1 + len(zfile.namelist())):
                if f"{i}.txt" in zfile.namelist():
                    data = zfile.read(f"{i}.txt").decode('utf-8')
                    audit_datas.append(create_text_data(data, f"{i}.txt"))
                elif f"{i}.jpg" in zfile.namelist():
                    data = zfile.read(f"{i}.jpg")
                    audit_datas.append(create_image_data(data, f"{i}.jpg"))
                elif f"{i}.mp4" in zfile.namelist():
                    data = zfile.read(f"{i}.mp4")
                    audit_datas.append(create_video_data(data, f"{i}.mp4"))
                elif f"{i}.mp3" in zfile.namelist():
                    data = zfile.read(f"{i}.mp3")
                    audit_datas.append(create_audio_data(data, f"{i}.mp3"))
                else:
                    flag = False
                    break
            if not flag:
                return_data = {
                    "files": audit_datas,
                    "upload_num": len(zfile.namelist()),
                    "legal_num": i - 1,
                }
                return request_failed(20, "file sequence interrupt", 200, data=return_data)
            return request_success(audit_datas)
        return request_failed(32, "data type error")
    else:
        return BAD_METHOD
