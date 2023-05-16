import json

from django.core.cache import cache
from django.http import HttpRequest

from task.models import Task, CurrentTagUser, update_task_tagger_list
from user.models import User
from user.vip_views import add_grow_value
from utils.utils_check import CheckLogin, CheckUser
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import CheckRequire, require


def pre_distribute(task_id: int, user: User):
    # 获取当前被分发到的user_id
    user_id = cache.get('current_user_id')
    if user_id is None:
        user_id = 1
        cache.set('current_user_id', user_id)
    task: Task = Task.objects.filter(task_id=task_id).first()
    if not task:
        return user_id, task, request_failed(14, "task not created", 404)
    if task.publisher != user:
        return user_id, task, request_failed(15, "no distribute permission")
    # 任务没被审核通过
    if task.check_result == "wait":
        return user_id, task, request_failed(34, "task not checked")
    if task.check_result == "refuse":
        return user_id, task, request_failed(33, "refused task")
    return user_id, task, None


@CheckLogin
@CheckUser
def distribute_task(req: HttpRequest, user: User, task_id: int):
    """
    分发任务
    """
    if req.method == "POST":
        user_id, task, err = pre_distribute(task_id, user)
        if err is not None:
            return err
        if task.current_tag_user_list.count() != 0 or task.strategy == "toall":
            return request_failed(22, "task has been distributed")
        # 顺序分发(根据标注方的信用分从高到低分发)
        tag_users = User.objects.filter(user_type="tag").all()
        # 设定的分发用户数比可分发的用户数多
        if task.distribute_user_num > tag_users.count() - User.objects.filter(is_banned=True).all().count():
            return request_failed(21, "tag user not enough")

        # 检测分数是否足够 扣分
        if user.score < task.reward_per_q * task.q_num * task.distribute_user_num:
            return request_failed(10, "score not enough")
        else:
            user.score -= task.reward_per_q * task.q_num * task.distribute_user_num
            user.save()
        add_grow_value(user, 10)
        current_tag_user_num = 0  # 当前被分发到的用户数
        while current_tag_user_num < task.distribute_user_num:
            if user_id >= tag_users[len(tag_users) - 1].user_id:
                tag_user = tag_users[0]
                user_id = tag_user.user_id
                # 检测是否在被封禁用户列表中
                if tag_user.is_banned:
                    continue
            else:
                user_id += 1
                tag_user = tag_users.filter(user_id=user_id).first()
                while not tag_user:
                    user_id += 1
                    tag_user = tag_users.filter(user_id=user_id).first()
                # 检测是否被封禁
                if tag_user.is_banned:
                    continue
            cache.set('current_user_id', user_id)
            current_tag_user = CurrentTagUser.objects.create(tag_user=tag_user)
            task.current_tag_user_list.add(current_tag_user)
            current_tag_user_num += 1
        task.save()
        return request_success()


@CheckLogin
@CheckUser
def redistribute_task(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        user_id, task, err = pre_distribute(task_id, user)
        task: Task = task
        if err is not None:
            return err
        if task.task_type == "toall":
            return request_failed(75, "toall task cannot redistribute")
        update_task_tagger_list(task)
        tag_users = User.objects.filter(user_type="tag").all()
        invalid_num = task.current_tag_user_list.filter(
            state__in=CurrentTagUser.invalid_state(),
            tag_user__user_id=user_id
        ).count()
        for ban_user in User.objects.filter(is_banned=True).all():
            if not task.current_tag_user_list.filter(
                    state__in=CurrentTagUser.invalid_state(),
                    tag_user=ban_user
            ).exists():
                invalid_num += 1
        if task.distribute_user_num > tag_users.count() - invalid_num:
            return request_failed(21, "tag user not enough")
        current_tag_user_num = task.current_tag_user_list.filter(
            state__in=CurrentTagUser.valid_state(),
            tag_user__user_id=user_id
        ).count()
        while current_tag_user_num < task.distribute_user_num:
            if user_id >= tag_users[len(tag_users) - 1].user_id:
                tag_user = tag_users[0]
                user_id = tag_user.user_id

            else:
                user_id += 1
                tag_user = tag_users.filter(user_id=user_id).first()
                while not tag_user:
                    user_id += 1
                    tag_user = tag_users.filter(user_id=user_id).first()
            # 检测是否在被封禁用户列表中
            if tag_user.is_banned:
                continue
            if task.current_tag_user_list.filter(tag_user=tag_user).exists():
                continue
            cache.set('current_user_id', user_id)
            current_tag_user = CurrentTagUser.objects.create(tag_user=tag_user)
            task.current_tag_user_list.add(current_tag_user)
            current_tag_user_num += 1
        task.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def to_agent(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        agent_id = require(body, "agent_id", "int", err_msg="invalid request", err_code=1005)
        agent = User.objects.filter(user_id=agent_id).first()
        if not agent:
            return request_failed(8, "user does not exist", 404)
        if agent.user_type != "agent":
            return request_failed(1006, "no permission")
        task = Task.objects.filter(task_id=task_id).first()
        if not task:
            return request_failed(14, "task not created", 404)
        if task.publisher != user:
            return request_failed(1006, "no permission")
        task.agent = agent
        task.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
def distribute_to_user(req: HttpRequest, user: User, task_id: int, user_id: int):
    """
    中介将任务分发给特定用户
    """
    if req.method == "POST":
        if user.user_type != "agent":
            return request_failed(1006, "no permission")
        task: Task = Task.objects.filter(task_id=task_id).first()
        if not task:
            return request_failed(14, "task not created", 404)
        if task.current_tag_user_list.filter(
                state__in=CurrentTagUser.valid_state()
        ).count() >= task.distribute_user_num:
            return request_failed(20, "The tasks have all been distributed")
        if task.current_tag_user_list.filter(
                state__in=CurrentTagUser.invalid_state(),
                tag_user__user_id=user_id
        ).exists():
            return request_failed(24, "user is distributed before")
        if task.current_tag_user_list.filter(tag_user__user_id=user_id).exists():
            return request_failed(25, "user has been distributed")

        cur_tag_user = CurrentTagUser.objects.create(tag_user=User.objects.filter(user_id=user_id).first())
        task.current_tag_user_list.add(cur_tag_user)
        task.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
def is_distributed(req: HttpRequest, user: User, task_id: int):
    """
    判断请求的任务是否已经被分发
    """
    if req.method == "GET":
        task: Task = Task.objects.filter(task_id=task_id).first()
        if not task:
            return request_failed(14, "task not created", 404)
        if task.agent or task.strategy == "toall":
            return request_success({"is_distributed": True})
        if task.current_tag_user_list.count() == 0:
            return request_success({"is_distributed": False})
        else:
            return request_success({"is_distributed": True})
    else:
        return BAD_METHOD
