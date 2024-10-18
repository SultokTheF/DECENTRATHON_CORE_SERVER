from django.contrib import admin
from .models import Center, Section, Subscription, Schedule, Record, SectionCategory, Feedback

@admin.register(SectionCategory)
class SectionCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'latitude', 'longitude', 'description')
    search_fields = ('name', 'location')
    list_filter = ('name',)
    filter_horizontal = ('users',)

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'center', 'description')
    search_fields = ('name', 'category__name', 'center__name')
    list_filter = ('category', 'center')
    readonly_fields = ('qr_code',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'start_date', 'end_date', 'is_active', 'is_activated_by_admin')
    search_fields = ('user__email', 'user__phone_number')
    list_filter = ('type', 'is_active', 'is_activated_by_admin')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('section', 'date', 'start_time', 'end_time', 'capacity', 'reserved', 'status')
    search_fields = ('section__name',)
    list_filter = ('section', 'date')

@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'schedule', 'attended', 'subscription')
    search_fields = ('user__email', 'user__phone_number')
    list_filter = ('attended',)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'center', 'stars', 'created_at')
    search_fields = ('user__email', 'center__name')
    list_filter = ('stars', 'center')

