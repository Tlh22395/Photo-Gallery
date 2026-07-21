from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path(
        "albums/<slug:slug>/",
        views.album_detail,
        name="album_detail",
    ),
    path(
        "photo/<int:photo_id>/download/",
        views.download_photo,
        name="download_photo",
    ),
    path(
        "photo/<int:photo_id>/checkout/",
        views.create_checkout_session,
        name="create_checkout_session",
    ),
    path(
        "payments/success/",
        views.payment_success,
        name="payment_success",
    ),
    path(
        "stripe/webhook/",
        views.stripe_webhook,
        name="stripe_webhook",
    ),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "dashboard/albums/new/",
        views.album_create,
        name="album_create",
    ),
    path(
        "dashboard/albums/<int:pk>/edit/",
        views.album_edit,
        name="album_edit",
    ),
    path(
        "dashboard/albums/<int:pk>/delete/",
        views.album_delete,
        name="album_delete",
    ),
    path(
        "dashboard/photos/new/",
        views.photo_create,
        name="photo_create",
    ),
    path(
        "dashboard/photos/<int:pk>/delete/",
        views.photo_delete,
        name="photo_delete",
    ),
    path(
        "dashboard/site/",
        views.site_edit,
        name="site_edit",
    ),
    path(
    "dashboard/photos/upload-multiple/",
    views.multiple_photo_upload,
    name="multiple_photo_upload",
),
]