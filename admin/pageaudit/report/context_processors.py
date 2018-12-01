from django.conf import settings

# Return any necessary/allowed values from settings.py here, to be used in templates.
# Usage is just like any other var using double braces. These just set global var.
def global_settings(request):
    return {
        'FORCE_SCRIPT_NAME': settings.FORCE_SCRIPT_NAME
    }
