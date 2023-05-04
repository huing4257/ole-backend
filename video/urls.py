from django.urls import path
import video.views as views

urlpatterns = [
    path('', views.upload),
    path('<path:video_url>', views.video_handler)
]
