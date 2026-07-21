from .models import SiteSettings
def site_settings(request):
    obj,_=SiteSettings.objects.get_or_create(pk=1)
    return {'site_settings':obj}
