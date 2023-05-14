from django.urls import path

import user.email_views
import user.face_views
import user.views as views
import user.vip_views as vip_views

urlpatterns = [
    path('register', views.register),
    path('login', views.login),
    path('logout', views.logout),
    path('userinfo/<user_id>', views.user_info),
    path('modifypassword', views.modify_password),
    path('ban_user/<int:user_id>', views.ban_user),
    path('get_all_users', views.get_all_users),
    path('getvip', vip_views.getvip),
    path('check_user/<int:user_id>', views.check_user),
    path('get_agent_list', views.get_agent_list),
    path('recharge', vip_views.recharge),
    path('withdraw', views.withdraw),
    path('get_verifycode', user.email_views.send_verify_code),
    path('get_all_tag_score', views.get_all_tag_score),
    path('modifybankaccount', views.modify_bank_card),
    path('change_email', user.email_views.change_email),
    path('modifypassword_by_email', user.email_views.modifypassword_by_email),
    path('verifycode_current_email', user.email_views.verifycode_current_email),
    path('face_recognition', user.face_views.face_reco),
    path('face_recognition_login', user.face_views.face_reco_login),
]
