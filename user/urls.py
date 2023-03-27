from django.urls import path
import user.views as views

urlpatterns = [
    path('register', views.register),
    path('login', views.login),
    path('logout', views.logout),
    path('userinfo', views.user_info),
    path('modifypassword', views.modify_password),
]
