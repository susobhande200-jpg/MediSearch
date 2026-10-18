import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('appointments','0001_initial'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='MedicalDocument', fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('title',models.CharField(max_length=180)),('kind',models.CharField(choices=[('report','Medical report'),('prescription','Prescription attachment'),('image','Medical image')],default='report',max_length=20)),('notes',models.TextField(blank=True)),('file',models.FileField(upload_to='medical_documents/%Y/%m/')),('created_at',models.DateTimeField(auto_now_add=True)),('appointment',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='documents',to='appointments.appointment')),('patient',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='medical_documents',to=settings.AUTH_USER_MODEL)),('uploaded_by',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='uploaded_medical_documents',to=settings.AUTH_USER_MODEL))])]
