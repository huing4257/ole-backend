import csv
import io
import json
import zipfile

from django.db.models import Q
from django.http import HttpRequest, HttpResponse

from picbed.models import Image
from task.models import Task, CurrentTagUser, TextData, Question, Result, InputResult, InputType
from user.models import User, UserCategory
from utils.utils_check import CheckLogin
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import CheckRequire
from utils.utils_time import get_timestamp, DAY
from video.models import Video


@CheckLogin
def refuse_task(req: HttpRequest, user: User, task_id: int):
    """
    后端收到该请求后，将任务分发给另一个不在past_tag_user_list中的标注用户，并更新current_tag_user_list。
    若剩余可分发用户不足，则返回错误响应。
    """
    if req.method == "POST":
        task: Task = Task.objects.filter(task_id=task_id).first()
        if not (task.current_tag_user_list.filter(tag_user=user).exists() or task.strategy == "toall"):
            return request_failed(18, "no permission to accept")
        current_tag_user: CurrentTagUser = task.current_tag_user_list.filter(tag_user=user).first()
        if current_tag_user is None:
            current_tag_user = CurrentTagUser.objects.create(tag_user=user)
            task.current_tag_user_list.add(current_tag_user)
        current_tag_user.accepted_at = -1
        current_tag_user.state = "refused"
        current_tag_user.save()
        task.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
def accept_task(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        # 计算一天之内接受的任务数目
        acc_num = CurrentTagUser.objects.filter(
            Q(tag_user=user) & Q(accepted_at__isnull=False) & Q(accepted_at__gte=get_timestamp() - DAY)).count()
        if acc_num >= max(int(user.credit_score / 10), 1):
            return request_failed(30, "accept limit")
        task: Task = Task.objects.filter(task_id=task_id).first()
        if task.strategy == "toall":
            if task.current_tag_user_list.filter(
                    state__in=CurrentTagUser.valid_state()
            ).count() >= task.distribute_user_num:
                return request_failed(31, "distribution completed")
            else:
                curr_tag_user: CurrentTagUser = task.current_tag_user_list.filter(tag_user=user).first()
                if curr_tag_user:
                    if curr_tag_user.state == "not_handle":
                        curr_tag_user.state = "accepted"
                        curr_tag_user.save()
                    else:
                        return request_failed(32, "repeat accept")
                else:
                    curr_tag_user = CurrentTagUser.objects.create(tag_user=user,
                                                                  accepted_at=get_timestamp(),
                                                                  state="accepted")
                    task.current_tag_user_list.add(curr_tag_user)
                task.save()
            return request_success()
        elif task.current_tag_user_list.filter(tag_user=user).exists():
            # current user is tag_user, change accepted_time
            current_tag_user = task.current_tag_user_list.filter(tag_user=user).first()
            current_tag_user.accepted_at = get_timestamp()
            current_tag_user.state = "accepted"
            current_tag_user.save()
            task.save()
            for category in task.task_style.all():
                user_category, created = UserCategory.objects.get_or_create(user=user, category=category)
                user_category.count += 1
                user_category.save()
            return request_success()
        else:
            # no permission to accept
            return request_failed(18, "no permission to accept")
    else:
        return BAD_METHOD


@CheckLogin
def get_progress(req: HttpRequest, user: User, task_id: int):
    if req.method == "GET":
        task = Task.objects.filter(task_id=task_id).first()
        if task.strategy == "toall" or task.current_tag_user_list.filter(tag_user=user).exists():
            if task.progress.filter(tag_user=user).first():
                # 已经做过这个题目
                qid = task.progress.filter(tag_user=user).first().q_id
                return request_success({"q_id": qid})
            else:
                # 这个用户还没做过这个题目
                return request_success({"q_id": 1})
        else:
            return request_failed(1006, "no access permission")
    else:
        return BAD_METHOD


@CheckLogin
def is_accepted(req: HttpRequest, user: User, task_id: int):
    """
    后端判断当前用户是否已经接受任务task_id。
    """
    if req.method == "GET":
        task: Task = Task.objects.filter(task_id=task_id).first()
        if not task:
            return request_failed(14, "task not created", 404)
        # 没有分发
        if task.strategy != "toall" and task.current_tag_user_list.count() == 0:
            return request_failed(22, "task not distributed", 400)
        for current_tag_user in task.current_tag_user_list.all():
            if current_tag_user.tag_user == user and current_tag_user.accepted_at:
                return request_success({"is_accepted": True})
        return request_success({"is_accepted": False})
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def taginfo(req, user: User, task_id):
    if req.method == "GET":
        task: Task = Task.objects.filter(task_id=task_id).first()
        if task is None:
            return request_failed(14, "task not created", 404)
        ret_data = []
        for question in task.questions.all():
            q_id = question.q_id

            result = question.result.filter(tag_user=user).first()
            if result is None:
                state = "notstarted"
                startat = None
                finishat = None
            else:
                startat = result.start_time
                finishat = result.finish_time
                state = "started" if finishat is None else "finished"

            q_type = question.data_type
            q_data = question.data
            if q_type == "text":
                q_data = TextData.objects.filter(id=int(q_data)).first().data
                if len(q_data) > 100:
                    q_data = q_data[:100]

            ret_data.append({
                "q_id": q_id,
                "state": state,
                "startat": startat,
                "finishat": finishat,
                "q_data": q_data,
                "q_type": q_type,
            })
        return request_success(ret_data)
    else:
        return BAD_METHOD


def get_question_filename(task: Task, filename):
    for q in task.questions.all():
        if q.filename() == filename:
            return q
    return None


@CheckLogin
@CheckRequire
def upload_many_res(req, user: User, task_id):
    if req.method == "POST":
        task: Task = Task.objects.filter(task_id=task_id).first()
        if task is None:
            return request_failed(14, "task not created", 404)
        if user.user_type != "tag":
            return request_failed(1006, "no permission")
        if task.task_type in ["threeD", "human_face", "image_select"]:
            return request_failed(72, "invalid task type")
        file_obj = req.FILES.get("file")
        file_data = file_obj.read().decode("utf-8")
        rows = csv.DictReader(io.StringIO(file_data), delimiter=',')
        if "filename" not in rows.fieldnames:
            return request_failed(71, "missing field name")
        if task.tag_type.exists() and "tag" not in rows.fieldnames:
            return request_failed(71, "missing field name")
        if task.task_type == "triplet" and any(tag not in rows.fieldnames for tag in ["first", "second"]):
            return request_failed(71, "missing field name")
        input_types = [input_type for input_type in task.input_type.all()]
        if any(input_type.input_tip not in rows.fieldnames for input_type in input_types):
            return request_failed(71, "missing field name")
        for row in rows:
            question: Question = get_question_filename(task, row["filename"])
            if question is None:
                return request_failed(73, "wrong filename")
            result: Result = question.result.filter(tag_user=user).first()
            if result is None:
                result = Result.objects.create(tag_user=user)
                question.result.add(result)
            if task.task_type == "triplet":
                result.tag_res = json.dumps([row["first"], row["second"]])
            elif task.task_type == "self_define":
                for input_type in input_types:
                    input_res = result.input_result.filter(input_type=input_type).first()
                    if input_res is None:
                        input_res = InputResult.objects.create(input_type=input_type)
                        result.input_result.add(input_res)
                    if input_type.tag_type.exists() and \
                            not input_type.tag_type.filter(type_name=row[input_type.input_tip]).exists():
                        return request_failed(74, "wrong tag name")
                    input_res.input_res = row[input_type.input_tip]
                    input_res.save()
            else:
                tags = [tag_type.type_name for tag_type in task.tag_type.all()]
                if row["tag"] not in tags:
                    return request_failed(74, "wrong tag name")
                result.tag_res = json.dumps(row['tag'])
            result.save()
            question.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def get_batch_data(req, user: User, task_id):
    if req.method == "GET":
        task: Task = Task.objects.filter(task_id=task_id).first()
        if task is None:
            return request_failed(14, "task not created", 404)
        if task.task_type in ["threeD", "human_face", "image_select"]:
            return request_failed(72, "invalid task type")
        if not task.current_tag_user_list.filter(tag_user=user, state="accepted").exists():
            return request_failed(1006, "no permission")

        file_name = "data.zip"
        response = HttpResponse(content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename={file_name}'
        response["Access-Control-Expose-Headers"] = "Content-Disposition"

        zip_buffer = io.BytesIO()
        ret_zip = zipfile.ZipFile(zip_buffer, "w")
        for question in task.questions.all():
            if question.data_type == "text":
                q_data: TextData = TextData.objects.filter(id=question.data).first()
                ret_zip.writestr(q_data.filename, q_data.data)
            elif question.data_type == "image":
                q_data: Image = Image.objects.filter(img_file=question.data[7:]).first()
                ret_zip.writestr(q_data.filename, q_data.img_file.read())
            else:  # question.data_type in ["video", "audio"]:
                q_data: Video = Video.objects.filter(video_file=question.data[6:]).first()
                ret_zip.writestr(q_data.filename, q_data.video_file.read())

        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        if task.task_type == "self_define":
            tag_input_types: list[InputType] = list(task.input_type.filter(tag_type__isnull=False))
            input_types: list[InputType] = list(task.input_type.filter(tag_type__isnull=True).all())
            writer.writerow(["filename"] + [tag_tip.input_tip for tag_tip in tag_input_types]
                            + [tag_tip.input_tip for tag_tip in input_types])
        elif task.task_type == "triplet":
            writer.writerow(["filename", "first", "second"])
        else:
            writer.writerow(["filename", "tag"])
        ret_zip.writestr("upload.csv", csv_buffer.getvalue())
        ret_zip.close()
        response.write(zip_buffer.getvalue())
        return response
    else:
        return BAD_METHOD
