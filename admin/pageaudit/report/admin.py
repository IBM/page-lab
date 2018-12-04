from django.contrib import admin

from .models import *

class LighthouseRunAdmin(admin.ModelAdmin):
    readonly_fields = ["url"]

class UrlAdmin(admin.ModelAdmin):
    search_fields = ["url"]
    readonly_fields = ["lighthouse_run", "url_kpi_average", "url_paths", "search_key_vals"]

class UrlKpiAverageAdmin(admin.ModelAdmin):
    readonly_fields = ["url"]

class LighthouseDataRawAdmin(admin.ModelAdmin):
    readonly_fields = ["lighthouse_run"]

class UserTimingMeasureAdmin(admin.ModelAdmin):
    readonly_fields = ["name", "url", "lighthouse_run"]

class UserTimingMeasureAverageAdmin(admin.ModelAdmin):
    readonly_fields = ["name", "url"]


admin.site.register(BannerNotification)
admin.site.register(LighthouseDataRaw, LighthouseDataRawAdmin)
admin.site.register(LighthouseDataUsertiming)
admin.site.register(LighthouseRun, LighthouseRunAdmin)
admin.site.register(PageView)
admin.site.register(Team)
admin.site.register(Url, UrlAdmin)
admin.site.register(UrlKpiAverage, UrlKpiAverageAdmin)
admin.site.register(UserTimingMeasure, UserTimingMeasureAdmin)
admin.site.register(UserTimingMeasureAverage, UserTimingMeasureAverageAdmin)
admin.site.register(UserTimingMeasureName)
admin.site.register(UrlFilter)
admin.site.register(UrlFilterPart)
admin.site.register(UrlOwner)
admin.site.register(SearchKeyVal)
admin.site.register(UrlPath)
