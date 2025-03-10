from django.contrib import admin
from .models import UrgentTask, RegularTask

# Register your models here.

admin.site.register(UrgentTask)
admin.site.register(RegularTask)


