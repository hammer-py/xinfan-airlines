"""Avatar rendering helpers.

The avatar can come from an uploaded file, a QQ sync, or nothing at all
(default icon). Uploaded files and QQ avatars are resources that can fail
to load, so the markup includes an onerror fallback that swaps in the
default icon rather than leaving the browser's broken-image placeholder
on the page.

Layout note: the avatar is rendered inside a fixed-size, self-centering
wrapper rather than as a bare inline <img>. A bare inline image sits on
the text baseline next to the hidden fallback span, which makes it drift
off-centre inside a text-center card. The wrapper is a flex box with auto
margins, so it is centred by geometry instead of by line-box rules.
"""

from django import template
from django.utils.html import format_html

register = template.Library()

# 固定尺寸 + 水平居中（auto margin）+ 内容居中（flex），不受父级排版影响
_WRAPPER = (
    '<span style="display:flex;width:{size}px;height:{size}px;'
    'margin-left:auto;margin-right:auto;'
    'align-items:center;justify-content:center;line-height:0">'
)

_ICON = (
    '<i class="bi bi-person-circle" '
    'style="font-size:{size}px;line-height:1;color:var(--accent)"></i>'
)

_IMG = (
    '<img src="{url}" alt="Avatar" style="display:block;width:{size}px;'
    'height:{size}px;border-radius:50%;object-fit:cover;'
    'object-position:center;border:{border}px solid var(--accent)" '
    'onerror="{onerror}">'
)


@register.simple_tag
def avatar(profile, size=100, border=3):
    """Render a user's avatar, or the default icon when there is none.

    size/border are pixel values so the same tag serves the large profile
    card and the smaller edit-page preview.
    """
    url = getattr(profile, 'avatar_url', None) if profile is not None else None

    if not url:
        return format_html(_WRAPPER + _ICON + '</span>', size=size)

    # 属性用双引号，因此 onerror 内部只能用单引号
    onerror = (
        "this.style.display='none';"
        "this.nextElementSibling.style.display='flex';"
    )
    return format_html(
        _WRAPPER
        + _IMG
        + '<span style="display:none;align-items:center;'
          'justify-content:center">'
        + _ICON
        + '</span></span>',
        url=url,
        size=size,
        border=border,
        onerror=onerror,
    )
