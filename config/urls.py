from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.contrib.auth import views as auth_views

def health(request):
    return JsonResponse({"status": "ok", "service": "MediSearch"})

admin.site.site_header = "MediSearch Control Center"
admin.site.site_title = "MediSearch Administration"
admin.site.index_title = "MediSearch pharmacy marketplace administration"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("profile/", include("profiles.urls")),
    path("", include("marketplace.urls")),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("appointments/", include("appointments.urls")),
    path("pharmacy/", include("pharmacy.urls")),
    path("health/", health, name="health"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/password-reset/", auth_views.PasswordResetView.as_view(template_name="registration/password_reset.html"), name="password_reset"),
]
