import json

from task.models import Task, ReportInfo
from user.models import User
from utils.utils_check import CheckLogin
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import CheckRequire, require


@CheckRequire
@CheckLogin
def report_user(req, user: User, task_id, user_id):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        reason = require(body, "reason", "string", err_msg="Missing or error type of [reason]")
        task: Task = Task.objects.filter(task_id=task_id).first()
        if task is None:
            return request_failed(33, "task not exists", 404)
        if task.publisher.user_id != user.user_id:
            return request_failed(1006, "no permission")
        reportee = User.objects.filter(user_id=user_id).first()
        if reportee is None or (
                task.current_tag_user_list.filter(tag_user=reportee).first() is None and task.publisher != reportee
        ):
            return request_failed(35, "user is not demand of this task", 404) if task.publisher != reportee else \
                request_failed(34, "user is not this task's tagger", 404)
        report_info: ReportInfo = ReportInfo.objects.filter(task=task, report_req=user, reportee=reportee).first()
        if report_info is None:
            ReportInfo.objects.create(task=task, report_req=user, reportee=reportee, reason=reason)
        else:
            report_info.reason = reason
            report_info.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def all_reports(req, user: User):
    if req.method == "GET":
        if user.user_type != "admin":
            return request_failed(1006, "no permission")
        return request_success([report_info.serialize() for report_info in ReportInfo.objects.filter(result=None)])
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def accept_report(req, user: User, task_id, user_id):
    if req.method == "POST":
        if user.user_type != "admin":
            return request_failed(1006, "no permission")
        tagger = User.objects.filter(user_id=user_id).first()
        task = Task.objects.filter(task_id=task_id).first()
        report_info = ReportInfo.objects.filter(reportee=tagger, task=task).first()
        if report_info is None:
            return request_failed(35, "report record not found", 404)
        report_info.result = True
        report_info.save()
        tagger = User.objects.filter(user_id=user_id).first()
        tagger.credit_score -= 10
        tagger.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def reject_report(req, user: User, task_id, user_id):
    if req.method == "POST":
        if user.user_type != "admin":
            return request_failed(1006, "no permission")
        report_info = ReportInfo.objects.filter(reportee_id=user_id, task_id=task_id).first()
        if report_info is None:
            return request_failed(35, "report record not found", 404)
        report_info.result = False
        report_info.save()
        return request_success()
    else:
        return BAD_METHOD
