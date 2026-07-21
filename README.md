# Photo Album Site

Working Django starter with:
- Public homepage and albums
- User signup/login/logout
- Authenticated photo downloads
- Preview watermark overlay
- Admin dashboard for albums, photos and homepage text/images
- Django advanced admin
- Download tracking

## Start
```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/
Admin dashboard: http://127.0.0.1:8000/dashboard/
Django admin: http://127.0.0.1:8000/django-admin/

## Important
This version allows any logged-in user to download enabled photos. Before charging money, add Stripe checkout/order verification and use S3 or Cloudinary for production file storage.
