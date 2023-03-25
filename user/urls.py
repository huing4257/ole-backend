from django.urls import path
import user.views as views

urlpatterns = [
    path('register', views.register),
    path('login', views.login),
    path('logout', views.logout),
]
