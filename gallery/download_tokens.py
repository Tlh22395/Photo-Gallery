# gallery/download_tokens.py

from django.core import signing

DOWNLOAD_SALT = "photo-store-download"


def create_download_token(purchase_id: int) -> str:
    return signing.dumps(
        {"purchase_id": purchase_id},
        salt=DOWNLOAD_SALT,
        compress=True,
    )


def read_download_token(
    token: str,
    max_age_seconds: int = 60 * 60 * 24 * 7,
) -> int:
    data = signing.loads(
        token,
        salt=DOWNLOAD_SALT,
        max_age=max_age_seconds,
    )

    return int(data["purchase_id"])