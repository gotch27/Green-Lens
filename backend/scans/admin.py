from django.contrib import admin

from .models import Result, Scan


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "location", "scanned_at")
    search_fields = ("location", "user__username", "user__email")
    list_filter = ("scanned_at",)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("id", "scan", "created_at")
    search_fields = ("scan__location", "diagnosis")
    list_filter = ("created_at",)
