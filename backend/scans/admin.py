from django.contrib import admin

from .models import Result, Scan


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "city", "temperature", "humidity", "scanned_at")
    search_fields = ("city", "user__username", "user__email")
    list_filter = ("scanned_at",)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("id", "scan", "is_sick", "confidence", "created_at")
    search_fields = ("scan__city", "diagnosis")
    list_filter = ("created_at",)
