from django.urls import path
import picbed.views as views

urlpatterns = [
    path('', views.upload),
    path('<path:img_url>', views.img_handler)
]
