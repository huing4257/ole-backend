import csv
import io
import json
import secrets

from django.http import HttpRequest, HttpResponse, JsonResponse

from review.models import AnsData, AnsList
from task.models import Task, Question, CurrentTagUser, Result, TagType, get_q_data, InputType
from user.models import User
from user.vip_views import add_grow_value
from utils.utils_check import CheckLogin
from utils.utils_request import request_success, BAD_METHOD, request_failed
from utils.utils_require import CheckRequire, require


# Create your views here.

def check_task(task_id: int, user: User) -> tuple[Task | None, JsonResponse | None]:
    task: Task = Task.objects.filter(task_id=task_id).first()
    if not task:
        return None, request_failed(14, "task not created", 404)
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
            return_q_data = question.serialize(detail=True, user_id=user_id)
            if task.task_type == "self_define":
                return_q_data["result"]["result"] = []
                return_q_data["result"]["input_result"] = []
                q_res: Result = question.result.filter(tag_user__user_id=user_id).first()
                for input_res in q_res.input_result.all():
                    if input_res.input_type.tag_type.exists():
                        return_q_data["result"]["result"].append(input_res.serialize())
                    else:
                        return_q_data["result"]["input_result"].append(input_res.serialize())
            return_data["q_info"].append(return_q_data)
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
        reader = csv.DictReader(io_string, delimiter=',')
        ans_list = AnsList.objects.create()
        if any(tag not in reader.fieldnames for tag in ["filename", "tag"]):
            return request_failed(20, "field error")
        for row in reader:
            ansdata = AnsData.objects.create(filename=row["filename"], std_ans=row["tag"])
            ansdata.save()
            ans_list.ans_list.add(ansdata)
        ans_list.save()
        return request_success(str(ans_list.id))
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
        task.save()
        if task.agent is not None:
            if task.current_tag_user_list.filter(state="check_accepted").count() == task.distribute_user_num:
                task.agent.score += int(task.reward_per_q * task.q_num * task.distribute_user_num * 1.4)
                task.agent.save()
                task.save()
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
        tag_input_types: list[InputType] = list(task.input_type.filter(tag_type__isnull=False))
        input_types: list[InputType] = list(task.input_type.filter(tag_type__isnull=True).all())
        if user_id is None:
            all_users: list[CurrentTagUser] = list(task.current_tag_user_list.filter(state="check_accepted").all())
            if len(all_users) != task.distribute_user_num:
                return request_failed(25, "review not finish")
            tags: list[TagType] = list(task.tag_type.all())
            if type == "all":
                if task.task_type == "self_define":
                    writer.writerow(["tag user", "filename"] + [tag_tip.input_tip for tag_tip in tag_input_types]
                                    + [tag_tip.input_tip for tag_tip in input_types])
                    for curr_tag_user in all_users:
                        for question in questions:
                            q_data = get_q_data(question)
                            tag_res: Result = question.result.filter(tag_user=curr_tag_user).first()
                            input_results = []
                            for input_type in tag_input_types:
                                input_results.append(
                                    tag_res.input_result.filter(input_type=input_type).first().input_res)
                            for input_type in input_types:
                                input_results.append(
                                    tag_res.input_result.filter(input_type=input_type).first().input_res)
                            writer.writerow([q_data.filename] + input_results)
                else:
                    writer.writerow(["filename"] + [tag.type_name for tag in tags])
                    for question in questions:
                        q_data = get_q_data(question)
                        res = [question.result.filter(tag_res=json.dumps(tag.type_name)).count() for tag in tags]
                        writer.writerow([q_data.filename] + res)
            else:
                if task.task_type in ["triplet", "image_select", "human_face", "threeD", "self_define"]:
                    return request_failed(80, "cannot merge this task type")
                else:
                    writer.writerow(["filename", "tag"])
                    for question in questions:
                        q_data = get_q_data(question)
                        res = [question.result.filter(tag_res=json.dumps(tag.type_name)).count() for tag in tags]
                        writer.writerow([q_data.filename, tags[res.index(max(res))].type_name])
        else:
            if task.task_type == "self_define":
                writer.writerow(["filename"] + [tag_tip.input_tip for tag_tip in tag_input_types]
                                + [tag_tip.input_tip for tag_tip in input_types])
                for question in questions:
                    q_data = get_q_data(question)
                    tag_res: Result = question.result.filter(tag_user=user_id).first()
                    input_results = []
                    for input_type in tag_input_types:
                        input_results.append(tag_res.input_result.filter(input_type=input_type).first().input_res)
                    for input_type in input_types:
                        input_results.append(tag_res.input_result.filter(input_type=input_type).first().input_res)
                    writer.writerow([q_data.filename] + input_results)
            else:
                writer.writerow(["filename", "tag"])
                for question in questions:
                    q_data = get_q_data(question)
                    tag_res: Result = question.result.filter(tag_user=user_id).first()
                    writer.writerow([q_data.filename, str(json.loads(tag_res.tag_res))])
        return response
    else:
        return BAD_METHOD
