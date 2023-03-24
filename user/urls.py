from django.urls import path
import user.views as views

urlpatterns = [
    path('login', views.login),
    path('logout', views.logout)
]
