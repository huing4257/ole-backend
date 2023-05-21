from django.urls import path

from advertise import views

urlpatterns = [
    path('publish', views.publish),
    path('get_ad', views.get_ad),
    path('get_my_ad', views.get_my_ad),
    path('renew/<int:ad_id>', views.renew),
]
