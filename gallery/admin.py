from django.contrib import admin
from .models import Album,Photo,SiteSettings,DownloadRecord
class PhotoInline(admin.TabularInline): model=Photo; extra=1
@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display=('title','is_published','created_at'); prepopulated_fields={'slug':('title',)}; inlines=[PhotoInline]
@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin): list_display=('title','album','is_downloadable','uploaded_at')
admin.site.register(SiteSettings)
admin.site.register(DownloadRecord)
