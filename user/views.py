from django.shortcuts import render
from django.http import HttpRequest,HttpResponse
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from django.contrib.auth import authenticate,login
from user.models import User
import json
import bcrypt

# Create your views here.
def login(req: HttpRequest):
    if req.method == "POST":
        #通过cookie判断是否已经登录
        if "userId" in req.COOKIES and "userName" in req.COOKIES and "userType" in req.COOKIES:
            return_data = {
                        "user_id": req.COOKIES["userId"],
                        "user_name": req.COOKIES["userName"],
                        "user_type": req.COOKIES["userType"],
                    }
            return request_success(return_data)

        body = json.loads(req.body.decode("utf-8"))
        uname = require(body,"user_name","string",err_msg="Missing or error type of name")
        upassword = require(body,"password","string",err_msg="Missing or error type of password")
        user:User = User.objects.filter(user_name=uname)
        if not user:
            return request_failed(4,"wrong username or password",400)
        else:
            if bcrypt.hashpw(upassword,bcrypt.gensalt()) == user.password:
                return_data = {
                        "user_id": user.user_id,
                        "user_name": user.user_name,
                        "user_type": user.user_type,
                    }
                response = request_success(return_data)
                response.set_cookie("userId",user.user_id)
                response.set_cookie("userName",user.user_name)
                response.set_cookie("userType",user.user_type)
                return response
            else:
                return request_failed(4,"wrong username or password",400)            
    else:
        return BAD_METHOD
    
def logout(req:HttpRequest):
    req.delete_cookie('userId')
    req.delete_cookie('userType')
    req.delete_cookie('userName')        
    return request_success()