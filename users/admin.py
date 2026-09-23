from django.contrib import admin

from .models import WaitlistEntry


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ['email', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['email']
    ordering = ['-created_at']
