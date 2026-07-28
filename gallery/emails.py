# gallery/emails.py

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from .download_tokens import create_download_token
from .models import Purchase


def send_purchase_download_email(
    purchase: Purchase,
    request=None,
) -> bool:
    if not purchase.user.email:
        return False

    token = create_download_token(purchase.id)

    relative_url = reverse(
        "purchase_download",
        kwargs={"token": token},
    )

    if request:
        download_url = request.build_absolute_uri(relative_url)
    else:
        site_url = settings.SITE_URL.rstrip("/")
        download_url = f"{site_url}{relative_url}"

    photo_title = (
        purchase.photo.title
        or purchase.photo.image.name
        or "Purchased photo"
    )

    subject = f"Your photo download: {photo_title}"

    message = f"""
Thank you for your purchase.

Your high-resolution photo is ready to download.

Photo: {photo_title}
Album: {purchase.photo.album.title}

Download your photo:
{download_url}

This download link expires in 7 days.

Please do not share this link with anyone else.

Thank you,
{getattr(settings, "SITE_NAME", "Photo Store")}
""".strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[purchase.user.email],
        fail_silently=False,
    )

    return True