import csv
import json
import secrets
import io

from django.http import HttpRequest, HttpResponse

from picbed.models import Image
from task.models import Task, Question, Current_tag_user, TextData, Result, TagType
from user.models import User
from review.models import AnsData, AnsList
from utils.utils_check import CheckLogin
from utils.utils_request import request_success, BAD_METHOD, request_failed
from utils.utils_require import CheckRequire, require


# Create your views here.

def check_task(task_id: int, user: User):
    task: Task = Task.objects.filter(task_id=task_id).first()
    if not task:
        return False, request_failed(14, "task not created", 400)
    if user != task.publisher:
        return False, request_failed(16, "no permissions")
    if task.current_tag_user_list.count() == 0:
        return False, request_failed(24, "task not distributed")
    return True, task


# 需求方人工审核
@CheckLogin
@CheckRequire
def manual_check(req: HttpRequest, user: User, task_id: int, user_id: int):
    if req.method == "POST":
        check_passed, task = check_task(task_id, user)
        if not check_passed:
            return task
        task: Task = task
        body = json.loads(req.body.decode("utf-8"))
        check_method = require(body, "check_method", err_msg="Missing or error type of [check_method]")
        if check_method == "select":  # 随机抽取任务总题数的1/10
            q_all_list = list(task.questions.all())
            q_num = len(q_all_list)  # 总题数
            # 如果总数过高，则不按比例抽取，固定抽取100道题，总数过低全抽
            check_num = 100 if q_num > 1000 else q_num // 10 if q_num > 100 else min(q_num, 10)
            q_list: list[Question] = secrets.SystemRandom().sample(q_all_list, check_num)
        else:  # 全量审核
            q_list: list[Question] = list(task.questions.all().order_by("q_id"))
        return_data = {"q_info": []}
        for question in q_list:
            return_data["q_info"].append(question.serialize(detail=True, user_id=user_id))
        return_data["q_info"].sort(key=lambda item: item['q_id'])
        return request_success(return_data)
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def upload_stdans(req: HttpRequest, user: User):
    if req.method == "POST":
        csv_file = req.FILES["file"]
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.reader(io_string, delimiter=',', quotechar='|')
        anslist = AnsList.objects.create()
        for row in reader:
            # print(row)
            if len(row) != 2:
                return request_failed(20, "field error")
            ansdata = AnsData.objects.create(filename=row[0], std_ans=row[1])
            ansdata.save()
            anslist.ans_list.add(ansdata)
        anslist.save()
        return request_success(str(anslist.id))
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def review_accept(req: HttpRequest, user: User, task_id: int, user_id: int):
    if req.method == "POST":
        check_passed, task = check_task(task_id, user)
        if not check_passed:
            return task
        task: Task = task
        curr_tag_user: Current_tag_user = task.current_tag_user_list.filter(tag_user=user_id).first()
        curr_tag_user.is_check_accepted = "pass"
        curr_tag_user.tag_user.score += task.reward_per_q * task.q_num  # 给标注方加分
        curr_tag_user.tag_user.save()
        curr_tag_user.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def review_reject(req: HttpRequest, user: User, task_id: int, user_id: int):
    if req.method == "POST":
        check_passed, task = check_task(task_id, user)
        if not check_passed:
            return task
        task: Task = task
        curr_tag_user: Current_tag_user = task.current_tag_user_list.filter(tag_user=user_id).first()
        curr_tag_user.is_check_accepted = "fail"
        curr_tag_user.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
# @CheckRequire
def download(req: HttpRequest, user: User, task_id: int, user_id: int = None):
    if req.method == "GET":
        type = req.GET.get("type")
        check_passed, task = check_task(task_id, user)
        if not check_passed:
            return task
        task: Task = task
        file_name = "result.csv"
        response = HttpResponse(content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename={file_name}'
        response["Access-Control-Expose-Headers"] = "Content-Disposition"

        writer = csv.writer(response)
        questions: list[Question] = list(task.questions.all())
        if user_id is None:
            all_users: list[Current_tag_user] = list(task.current_tag_user_list.all())
            for tag_user in all_users:
                if tag_user.is_check_accepted == "none":
                    return request_failed(25, "review not finish")
            tags: list[TagType] = list(task.tag_type.all())
            if type == "all":
                if task.task_type == "text":
                    writer.writerow(["filename"] + [tag.type_name for tag in tags])
                    for question in questions:
                        text_data: TextData = TextData.objects.filter(id=question.data).first()
                        res = [question.result.filter(tag_res=tag.type_name).count() for tag in tags]
                        writer.writerow([text_data.filename] + res)
                elif task.task_type == "image":
                    writer.writerow(["filename"] + [tag.type_name for tag in tags])
                    for question in questions:
                        img_data: Image = Image.objects.filter(img_file=question.data[7:]).first()
                        res = [question.result.filter(tag_res=tag.type_name).count() for tag in tags]
                        writer.writerow([img_data.filename] + res)
            else:
                if task.task_type == "text":
                    for question in questions:
                        text_data: TextData = TextData.objects.filter(id=question.data).first()
                        res = [question.result.filter(tag_res=tag.type_name).count() for tag in tags]
                        writer.writerow([text_data.filename, tags[res.index(max(res))].type_name])
                elif task.task_type == "image":
                    for question in questions:
                        img_data: Image = Image.objects.filter(img_file=question.data[7:]).first()
                        res = [question.result.filter(tag_res=tag.type_name).count() for tag in tags]
                        writer.writerow([img_data.filename, tags[res.index(max(res))].type_name])
        else:
            if task.task_type == "text":
                for question in questions:
                    text_data: TextData = TextData.objects.filter(id=question.data).first()
                    tag_res: Result = question.result.filter(tag_user=user_id).first()
                    writer.writerow([text_data.filename, tag_res.tag_res])
            elif task.task_type == "image":
                for question in questions:
                    img_data: Image = Image.objects.filter(img_file=question.data[7:]).first()
                    tag_res: Result = question.result.filter(tag_user=user_id).first()
                    writer.writerow([img_data.filename, tag_res.tag_res])

        return response
    else:
        return BAD_METHOD
