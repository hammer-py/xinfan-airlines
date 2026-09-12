"""Avatar rendering helpers.

The avatar can come from three places: an uploaded file, a QQ number, or
nothing at all (default icon). Uploaded files and QQ avatars are both
resources that can fail to load, so the markup includes an onerror
fallback that swaps in the default icon rather than leaving the browser's
broken-image placeholder on the page.
"""

from django import template
from django.utils.html import format_html

register = template.Library()

_FALLBACK_ICON = (
    '<i class="bi bi-person-circle" '
    'style="font-size:{size}px;color:var(--accent)"></i>'
)


@register.simple_tag
def avatar(profile, size=100, border=3):
    """Render a user's avatar, or the default icon when there is none.

    size/border are pixel values so the same tag serves the large profile
    card and the smaller edit-page preview.
    """
    if profile is None:
        return format_html(_FALLBACK_ICON, size=size)

    url = getattr(profile, 'avatar_url', None)
    if not url:
        return format_html(_FALLBACK_ICON, size=size)

    # 属性用双引号，因此 onerror 内部只能用单引号。
    onerror = (
        "this.style.display='none';"
        "this.nextElementSibling.style.display='inline-block';"
    )
    return format_html(
        '<img src="{}" alt="Avatar" style="width:{size}px;height:{size}px;'
        'border-radius:50%;object-fit:cover;border:{border}px solid var(--accent)" '
        'onerror="{onerror}">'
        '<span style="display:none">{fallback}</span>',
        url,
        size=size,
        border=border,
        onerror=onerror,
        fallback=format_html(_FALLBACK_ICON, size=size),
    )
