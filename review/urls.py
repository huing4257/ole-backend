from django.urls import path
import review.views as views

urlpatterns = [
    path('manual_check/<int:task_id>/<int:user_id>', views.manual_check),
    path('refuse/<int:task_id>/<int:user_id>', views.review_reject),
    path('accept/<int:task_id>/<int:user_id>', views.review_accept),
    path('download/<int:task_id>/<int:user_id>', views.download),
    path('download/<int:task_id>', views.download),
    path('upload_stdans', views.upload_stdans),
    path('report/<int:task_id>/<int:user_id>', views.report_user),
    path('reportmessage', views.all_reports),
    path('acceptreport/<int:task_id>/<int:user_id>', views.accept_report),
    path('rejectreport/<int:task_id>/<int:user_id>', views.reject_report)
]
