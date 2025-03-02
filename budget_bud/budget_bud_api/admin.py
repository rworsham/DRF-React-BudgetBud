from django.contrib import admin
from .models import Report, ReportDashboard
from django_apscheduler.models import DjangoJob, DjangoJobExecution


class ReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name')
    search_fields = ('name', 'display_name')
    list_filter = ('name',)

class ReportDashboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'report', 'x_size', 'y_size')
    list_filter = ('x_size', 'y_size')
    search_fields = ('user__username', 'report__name')

admin.site.register(Report, ReportAdmin)
admin.site.register(ReportDashboard, ReportDashboardAdmin)
