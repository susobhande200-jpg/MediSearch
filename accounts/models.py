from django.conf import settings
from django.db import models

class PatientProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="patient_profile")
    phone = models.CharField(max_length=25, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=120, blank=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.user.get_full_name() or self.user.username

class StaffProfile(models.Model):
    class Role(models.TextChoices):
        DOCTOR = "doctor", "Doctor"
        RECEPTIONIST = "receptionist", "Receptionist"
        NURSE = "nurse", "Nurse / Medical Staff"
        PHARMACIST = "pharmacist", "Pharmacist"
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff_profile")
    role = models.CharField(max_length=20, choices=Role.choices)
    phone = models.CharField(max_length=25, blank=True)
    is_approved = models.BooleanField(default=False)
    def __str__(self): return f"{self.user.username} ({self.role})"

class ClinicMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='clinic_messages_sent')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='clinic_messages_received')
    body = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    class Meta: ordering = ['created_at']
    def __str__(self): return f'{self.sender} → {self.recipient}: {self.body[:50]}'
