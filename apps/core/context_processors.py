from django.conf import settings


def turnstile(request):
    """把 Turnstile 站点密钥暴露给模板，避免在模板里硬编码。"""
    return {'turnstile_site_key': settings.TURNSTILE_SITE_KEY}
