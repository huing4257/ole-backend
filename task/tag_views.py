from django.db.models import Q
from django.http import HttpRequest

from task.models import Task, CurrentTagUser
from user.models import User, UserCategory
from utils.utils_check import CheckLogin
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_time import get_timestamp, DAY


@CheckLogin
def refuse_task(req: HttpRequest, user: User, task_id: int):
    """
    后端收到该请求后，将任务分发给另一个不在past_tag_user_list中的标注用户，并更新current_tag_user_list。
    若剩余可分发用户不足，则返回错误响应。
    """
    if req.method == "POST":
        task = Task.objects.filter(task_id=task_id).first()
        if not task.current_tag_user_list.filter(tag_user=user).exists():
            return request_failed(18, "no permission to accept")
        current_tag_user = task.current_tag_user_list.filter(tag_user=user).first()
        current_tag_user.accepted_at = -1
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
        print(acc_num)
        if acc_num >= 10:
            return request_failed(30, "accept limit")
        task = Task.objects.filter(task_id=task_id).first()
        if task.strategy == "toall":
            if task.current_tag_user_list.filter(accepted_at__gte=0).count() >= task.distribute_user_num:
                return request_failed(31, "distribution completed")
            else:
                if task.current_tag_user_list.filter(tag_user=user, accepted_at__gte=0).exists():
                    return request_failed(32, "repeat accept")
                curr_tag_user = CurrentTagUser.objects.create(tag_user=user, accepted_at=get_timestamp())
                task.current_tag_user_list.add(curr_tag_user)
                task.save()
        if task.current_tag_user_list.filter(tag_user=user).exists():
            # current user is tag_user, change accepted_time
            for current_tag_user in task.current_tag_user_list.all():
                if current_tag_user.tag_user == user:
                    current_tag_user.accepted_at = get_timestamp()
                    current_tag_user.save()
            task.save()
            for category in task.task_style.all():
                user_category, created = UserCategory.objects.get_or_create(user=user, category=category)
                user_category.count += 1
                user_category.save()
            return request_success(task.serialize())
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


