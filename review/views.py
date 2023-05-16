import csv
import json
import secrets
import io

from django.http import HttpRequest, HttpResponse, JsonResponse

from task.models import Task, Question, CurrentTagUser, Result, TagType, get_q_data, InputType, InputResult
from user.models import User
from user.vip_views import add_grow_value
from review.models import AnsData, AnsList
from utils.utils_check import CheckLogin
from utils.utils_request import request_success, BAD_METHOD, request_failed
from utils.utils_require import CheckRequire, require


# Create your views here.

def check_task(task_id: int, user: User) -> tuple[Task | None, JsonResponse | None]:
    task: Task = Task.objects.filter(task_id=task_id).first()
    if not task:
        return None, request_failed(14, "task not created", 400)
    if user != task.publisher and user.user_type != "admin":
        return None, request_failed(16, "no permissions")
    if task.current_tag_user_list.count() == 0:
        return None, request_failed(24, "task not distributed")
    return task, None


@CheckLogin
@CheckRequire
def manual_check(req: HttpRequest, user: User, task_id: int, user_id: int):
    """
    需求方人工审核
    """
    if req.method == "POST":
        task, err = check_task(task_id, user)
        if err is not None:
            return err
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
        task, err = check_task(task_id, user)
        if err is not None:
            return err
        curr_tag_user: CurrentTagUser = task.current_tag_user_list.filter(tag_user=user_id).first()
        curr_tag_user.state = "check_accepted"
        curr_tag_user.tag_user.tag_score += task.reward_per_q * task.q_num  # 给标注方加分
        curr_tag_user.tag_user.score += task.reward_per_q * task.q_num  # 给标注方加分
        add_grow_value(curr_tag_user.tag_user, 10)
        curr_tag_user.tag_user.save()
        curr_tag_user.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def review_reject(req: HttpRequest, user: User, task_id: int, user_id: int):
    if req.method == "POST":
        task, err = check_task(task_id, user)
        if err is not None:
            return err
        curr_tag_user: CurrentTagUser = task.current_tag_user_list.filter(tag_user=user_id).first()
        curr_tag_user.state = "check_refused"
        curr_tag_user.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def download(req: HttpRequest, user: User, task_id: int, user_id: int = None):
    if req.method == "GET":
        type = req.GET.get("type")
        task, err = check_task(task_id, user)
        if err is not None:
            return err
        file_name = "result.csv"
        response = HttpResponse(content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename={file_name}'
        response["Access-Control-Expose-Headers"] = "Content-Disposition"

        questions: list[Question] = list(task.questions.all())
        writer = csv.writer(response)
        input_types: list[InputType] = list(task.input_type.all())
        if user_id is None:
            all_users: list[CurrentTagUser] = list(task.current_tag_user_list.filter(state="check_accepted").all())
            if len(all_users) != task.distribute_user_num:
                return request_failed(25, "review not finish")
            tags: list[TagType] = list(task.tag_type.all())
            if type == "all":
                writer.writerow(["filename"] + [tag.type_name for tag in tags])
                for question in questions:
                    q_data = get_q_data(question)
                    res = [question.result.filter(tag_res=tag.type_name).count() for tag in tags]
                    writer.writerow([q_data.filename] + res)
            else:
                for question in questions:
                    q_data = get_q_data(question)
                    res = [question.result.filter(tag_res=tag.type_name).count() for tag in tags]
                    writer.writerow([q_data.filename, tags[res.index(max(res))].type_name])
        else:
            writer.writerow(["filename", "tag"] + [input_type.input_tip for input_type in input_types])
            for question in questions:
                q_data = get_q_data(question)
                tag_res: Result = question.result.filter(tag_user=user_id).first()
                input_results = []
                for input_type in input_types:
                    input_res: InputResult = tag_res.input_result.filter(input_type=input_type).first()
                    input_results.append(input_res.input_res)
                writer.writerow([q_data.filename, str(json.loads(tag_res.tag_res))] + input_results)

        return response
    else:
        return BAD_METHOD
