from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_picture_preview', 'birthday', 'website')
    search_fields = ('user__username', 'user__email', 'biography', 'website')
    list_filter = ('birthday',)
    readonly_fields = ('profile_picture_preview', 'banner_picture_preview')
    ordering = ('user__username',)
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'birthday', 'biography')
        }),
        ('Profile Pictures', {
            'fields': ('profile_picture', 'banner_picture')
        }),
        ('Social Links', {
            'fields': ('website', 'instagram', 'facebook', 'threads', 'linkedin', 'youtube', 'tiktok', 'github', 'gitlab')
        }),
    )