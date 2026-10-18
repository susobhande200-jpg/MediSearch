from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core import signing
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User
from .forms import PatientRegistrationForm
from .models import PatientProfile, StaffProfile
from appointments.models import Appointment, ConsultationNote, Prescription, MedicalRecord

def register(request):
    if request.user.is_authenticated:
        return redirect("customer_dashboard")
    if request.method == "POST":
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            token = signing.dumps({"user_id": user.pk}, salt="medikhoj-email-verification")
            verify_url = request.build_absolute_uri(reverse("verify_email", args=[token]))
            try:
                send_mail("Verify your MediSearch email", f"Hello {user.first_name},\n\nVerify your email by opening:\n{verify_url}\n\nIf you did not create this account, ignore this email.", settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
                messages.success(request, "Account created. Check your email for the verification link.")
            except Exception:
                messages.warning(request, "Account created, but email delivery is not configured. Ask the administrator to configure SMTP.")
            login(request, user)
            return redirect("customer_dashboard")
    else:
        form = PatientRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})

def verify_email(request, token):
    try:
        data = signing.loads(token, salt="medikhoj-email-verification", max_age=60*60*24)
        user = get_object_or_404(User, pk=data["user_id"])
        profile, _ = PatientProfile.objects.get_or_create(user=user)
        profile.email_verified = True
        profile.save(update_fields=["email_verified"])
        messages.success(request, "Email verified successfully.")
    except (signing.BadSignature, signing.SignatureExpired, KeyError, TypeError):
        messages.error(request, "This verification link is invalid or has expired.")
    return redirect("login")

@login_required
def dashboard(request):
    appointments = Appointment.objects.filter(patient=request.user).select_related("doctor__user", "doctor__department").order_by("-appointment_date", "-start_time")
    records = MedicalRecord.objects.filter(patient=request.user).order_by("-created_at")[:5]
    prescriptions = Prescription.objects.filter(patient=request.user).order_by("-created_at")[:5]
    return render(request, "accounts/dashboard.html", {"appointments": appointments[:10], "total_appointments": appointments.count(), "records": records, "prescriptions": prescriptions})

@login_required
def role_dashboard(request):
    profile = getattr(request.user, "staff_profile", None)
    if not request.user.is_staff and not profile:
        messages.error(request, "This dashboard is for authorized clinic staff.")
        return redirect("dashboard")
    if request.user.is_staff:
        return redirect("/admin/")
    if not profile.is_approved:
        return render(request, "accounts/staff_pending.html", {"profile": profile})
    if profile.role == StaffProfile.Role.DOCTOR:
        appointments = Appointment.objects.filter(doctor__user=request.user).select_related("patient", "doctor__department").order_by("appointment_date", "start_time")
        return render(request, "accounts/doctor_dashboard.html", {"appointments": appointments})
    appointments = Appointment.objects.filter(status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED]).select_related("patient", "doctor__user").order_by("appointment_date", "start_time")
    if profile.role == StaffProfile.Role.RECEPTIONIST:
        return render(request, "accounts/reception_dashboard.html", {"appointments": appointments})
    if profile.role == StaffProfile.Role.NURSE:
        return render(request, "accounts/medical_staff_dashboard.html", {"profile": profile, "appointments": appointments, "dashboard_role": "Nurse / Medical Staff", "dashboard_icon": "bi-heart-pulse", "help_text": "Review appointment queues, coordinate with doctors, and track patient flow. Clinical access is limited to authorized workflows."})
    if profile.role == StaffProfile.Role.PHARMACIST:
        prescriptions = Prescription.objects.select_related("patient", "doctor__user", "appointment").order_by("-created_at")[:100]
        return render(request, "accounts/pharmacist_dashboard.html", {"profile": profile, "prescriptions": prescriptions})
    messages.error(request, "Your staff role is not configured. Contact the administrator.")
    return redirect("dashboard")


@login_required
def control_center(request):
    """Organized overview for Django superusers and authorized clinic admins."""
    if not request.user.is_staff:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    from django.contrib.auth.models import User
    from core.models import Department, DoctorProfile
    from appointments.models import Payment, ChatMessage
    from django.utils import timezone
    today = timezone.localdate()
    context = {
        "patient_count": PatientProfile.objects.count(),
        "staff_count": StaffProfile.objects.count(),
        "doctor_count": DoctorProfile.objects.count(),
        "department_count": Department.objects.count(),
        "appointment_count": Appointment.objects.count(),
        "pending_count": Appointment.objects.filter(status=Appointment.Status.PENDING).count(),
        "today_count": Appointment.objects.filter(appointment_date=today).count(),
        "completed_count": Appointment.objects.filter(status=Appointment.Status.COMPLETED).count(),
        "payment_count": Payment.objects.count(),
        "unapproved_staff": StaffProfile.objects.filter(is_approved=False).select_related("user")[:8],
        "recent_appointments": Appointment.objects.select_related("patient", "doctor__user").order_by("-created_at")[:8],
    }
    return render(request, "accounts/control_center.html", context)

@login_required
def clinic_chat(request):
    """Private staff-to-staff inbox for approved clinic users and administrators."""
    from django.core.exceptions import PermissionDenied
    from django.db.models import Q
    from django.utils import timezone
    from .models import ClinicMessage
    profile = getattr(request.user, 'staff_profile', None)
    if not (request.user.is_staff or request.user.is_superuser or (profile and profile.is_approved)):
        raise PermissionDenied
    people = User.objects.filter(Q(is_staff=True) | Q(staff_profile__is_approved=True)).exclude(pk=request.user.pk).distinct().order_by('first_name','username')
    selected = request.GET.get('with') or request.POST.get('recipient')
    partner = get_object_or_404(people, pk=selected) if selected else None
    if request.method == 'POST':
        body = request.POST.get('body','').strip()
        if not partner or not body:
            messages.error(request, 'Choose a colleague and enter a message.')
        elif len(body) > 3000:
            messages.error(request, 'Messages must be 3,000 characters or fewer.')
        else:
            ClinicMessage.objects.create(sender=request.user, recipient=partner, body=body)
            return redirect(f'{reverse("clinic_chat")}?with={partner.pk}')
    if partner:
        thread = ClinicMessage.objects.filter(Q(sender=request.user, recipient=partner) | Q(sender=partner, recipient=request.user)).select_related('sender','recipient')
    else:
        thread = ClinicMessage.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).select_related('sender','recipient')
    if partner:
        ClinicMessage.objects.filter(sender=partner, recipient=request.user, read_at__isnull=True).update(read_at=timezone.now())
    return render(request, 'accounts/clinic_chat.html', {'people':people,'partner':partner,'thread':thread,'unread_count':ClinicMessage.objects.filter(recipient=request.user,read_at__isnull=True).count()})
