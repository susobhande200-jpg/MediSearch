from django.urls import path
from . import views
urlpatterns = [
    path("doctors/", views.doctor_list, name="doctors"),
    path("doctors/<int:pk>/", views.doctor_detail, name="doctor_detail"),
]
