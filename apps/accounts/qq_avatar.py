"""Server-side QQ avatar fetching.

QQ avatars live on qlogo.cn, which is unreachable from some client
networks (connection reset at the TLS handshake). Fetching it from the
server and storing it as a normal uploaded file sidesteps that: the
browser only ever talks to our own domain.

Returns the stored file on success, None on any failure, so callers can
tell the user instead of silently rendering an empty avatar.
"""

import urllib.error
import urllib.request

from django.core.files.base import ContentFile

# 腾讯有多个头像节点，q1 不通时依次尝试其余的
QLOGO_HOSTS = ('q1', 'q2', 'q3', 'q4')

MAX_BYTES = 2 * 1024 * 1024
TIMEOUT_SECONDS = 10

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
    ),
    'Referer': 'https://user.qzone.qq.com/',
    'Accept': 'image/avif,image/webp,image/png,image/*,*/*;q=0.8',
}


def fetch_qq_avatar(qq_number, size=100):
    """下载 QQ 头像，成功返回 ContentFile，失败返回 None。

    任何异常都被吞掉并转成 None —— 调用方需要的是"能不能拿到"这个
    布尔事实，而不是异常类型。
    """
    qq_number = (qq_number or '').strip()
    if not qq_number.isdigit():
        return None

    for host in QLOGO_HOSTS:
        url = f'https://{host}.qlogo.cn/g?b=qq&nk={qq_number}&s={size}'
        try:
            request = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                if response.status != 200:
                    continue
                content_type = (response.headers.get('Content-Type') or '').lower()
                if not content_type.startswith('image/'):
                    continue
                data = response.read(MAX_BYTES + 1)
                if not data or len(data) > MAX_BYTES:
                    continue
                return ContentFile(data, name=f'qq_{qq_number}.png')
        except (urllib.error.URLError, OSError, ValueError):
            # 这个节点不通，换下一个
            continue

    return None
