import json

from advertise.models import Advertise
from user.models import User
from utils.utils_check import CheckLogin
from utils.utils_request import BAD_METHOD, request_failed, request_success
from utils.utils_require import CheckRequire, require
from utils.utils_time import get_timestamp


# Create your views here.
@CheckLogin
@CheckRequire
def publish(req, user: User):
    if req.method == "POST":
        if user.user_type != "advertiser":
            return request_failed(1006, "no permission")
        body = json.loads(req.body.decode("utf-8"))
        ad_time = require(body, "time", "int", err_msg="Missing or error type of [time]")
        ad_type = require(body, "type", "string", err_msg="Missing or error type of [type]")
        img_url = require(body, "url", "string", err_msg="Missing or error type of [url]")
        if user.score < ad_time:
            return request_failed(83, "score not enough")
        user.score -= ad_time
        user.save()
        Advertise.objects.create(
            ad_time=get_timestamp() + ad_time,
            ad_type=ad_type,
            img_url=img_url,
            publisher=user,
            ad_pub_time=get_timestamp()
        )
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def get_ad(req, user: User):
    if req.method == "GET":
        ad_type = req.GET.get('type', default='horizontal')
        num = req.GET.get('num', default=4)
        num = int(num)
        ads = Advertise.objects.filter(ad_type=ad_type, ad_time__gte=get_timestamp())
        ads = ads.order_by('?')[:min(ads.count(), num)]
        return request_success([ad.img_url for ad in ads])
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def renew(req, user: User, ad_id):
    if req.method == "POST":
        if user.user_type != "advertiser":
            return request_failed(1006, "no permission")
        body = json.loads(req.body.decode("utf-8"))
        ad_time = require(body, "time", "int", err_msg="Missing or error type of [time]")
        ad: Advertise = Advertise.objects.filter(ad_id=ad_id).first()
        if ad is None:
            return request_failed(86, "no such ad")
        if user.score < ad_time:
            return request_failed(83, "score not enough")
        user.score -= ad_time
        user.save()
        ad.ad_time = max(get_timestamp(), ad.ad_time) + ad_time
        ad.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def get_my_ad(req, user: User):
    if req.method == "GET":
        if user.user_type != "advertiser":
            return request_failed(1006, "no permission")
        return request_success([ad.serialize() for ad in Advertise.objects.filter(publisher=user)])
    else:
        return BAD_METHOD
