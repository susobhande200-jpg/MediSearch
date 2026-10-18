from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
   
    



    # Existing project routes
    path("register/", views.register, name="register"),
    path("verify/<str:token>/", views.verify_email, name="verify_email"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("staff-dashboard/", views.role_dashboard, name="staff_dashboard"),
    path("control-center/", views.control_center, name="control_center"),
    path("clinic-chat/", views.clinic_chat, name="clinic_chat"),
]