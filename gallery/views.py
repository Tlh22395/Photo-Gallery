from pathlib import Path
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required,user_passes_test
from django.http import FileResponse,Http404
from django.shortcuts import render,redirect,get_object_or_404
from .models import Album,Photo,SiteSettings,DownloadRecord
from .forms import SignupForm,AlbumForm,PhotoForm,SiteSettingsForm
import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .models import Photo, Purchase


stripe.api_key = settings.STRIPE_SECRET_KEY


def home(request): return render(request,'gallery/home.html',{'albums':Album.objects.filter(is_published=True)})
def album_detail(request,slug): return render(request,'gallery/album_detail.html',{'album':get_object_or_404(Album,slug=slug,is_published=True)})
def signup_view(request):
    form=SignupForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save(); login(request,user); messages.success(request,'Account created.'); return redirect('home')
    return render(request,'registration/signup.html',{'form':form})
def login_view(request):
    if request.method=='POST':
        user=authenticate(request,username=request.POST.get('username'),password=request.POST.get('password'))
        if user: login(request,user); return redirect(request.GET.get('next') or 'home')
        messages.error(request,'Invalid username or password.')
    return render(request,'registration/login.html')
def logout_view(request): logout(request); return redirect('home')
@login_required
def download_photo(request, photo_id):
    photo = get_object_or_404(
        Photo,
        pk=photo_id,
        is_downloadable=True
    )

    has_purchased = Purchase.objects.filter(
        user=request.user,
        photo=photo,
        status="paid",
    ).exists()

    if not has_purchased and not request.user.is_staff:
        return HttpResponse(
            "You must purchase this photo before downloading it.",
            status=403,
        )

    file_path = Path(photo.image.path)

    if not file_path.exists():
        raise Http404("File not found")

    DownloadRecord.objects.create(
        user=request.user,
        photo=photo,
    )

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=file_path.name,
    )
def staff(view): return user_passes_test(lambda u:u.is_staff)(view)
@staff
def dashboard(request): return render(request,'gallery/dashboard.html',{'albums':Album.objects.all(),'photos':Photo.objects.select_related('album')[:30],'download_count':DownloadRecord.objects.count()})
@staff
def album_create(request):
    form=AlbumForm(request.POST or None,request.FILES or None)
    if request.method=='POST' and form.is_valid(): form.save(); return redirect('dashboard')
    return render(request,'gallery/form.html',{'form':form,'title':'Create album'})
@staff
def album_edit(request,pk):
    obj=get_object_or_404(Album,pk=pk); form=AlbumForm(request.POST or None,request.FILES or None,instance=obj)
    if request.method=='POST' and form.is_valid(): form.save(); return redirect('dashboard')
    return render(request,'gallery/form.html',{'form':form,'title':'Edit album'})
@staff
def album_delete(request,pk):
    obj=get_object_or_404(Album,pk=pk)
    if request.method=='POST': obj.delete(); return redirect('dashboard')
    return render(request,'gallery/confirm.html',{'object':obj})
@staff
def photo_create(request):
    form=PhotoForm(request.POST or None,request.FILES or None)
    if request.method=='POST' and form.is_valid(): form.save(); return redirect('dashboard')
    return render(request,'gallery/form.html',{'form':form,'title':'Upload photo'})
@staff
def photo_delete(request,pk):
    obj=get_object_or_404(Photo,pk=pk)
    if request.method=='POST': obj.delete(); return redirect('dashboard')
    return render(request,'gallery/confirm.html',{'object':obj})
@staff
def site_edit(request):
    obj,_=SiteSettings.objects.get_or_create(pk=1); form=SiteSettingsForm(request.POST or None,request.FILES or None,instance=obj)
    if request.method=='POST' and form.is_valid(): form.save(); return redirect('dashboard')
    return render(request,'gallery/form.html',{'form':form,'title':'Edit homepage'})
@login_required
def create_checkout_session(request, photo_id):
    if request.method != "POST":
        return redirect("home")

    photo = get_object_or_404(Photo, pk=photo_id)

    purchase = Purchase.objects.create(
        user=request.user,
        photo=photo,
        status="pending",
    )

    try:
        checkout_session = stripe.checkout.Session.create(
    mode="payment",
    line_items=[
        {
            "price_data": {
                "currency": "usd",
                "unit_amount": photo.price_cents,
                "product_data": {
                    "name": photo.title or "Photo",
                },
            },
            "quantity": 1,
        }
    ],
    success_url=(
        request.build_absolute_uri(reverse("payment_success"))
        + "?session_id={CHECKOUT_SESSION_ID}"
    ),
    cancel_url=request.build_absolute_uri(
        reverse("album_detail", args=[photo.album.slug])
    ),
    metadata={
        "photo_id": str(photo.id),
        "user_id": str(request.user.id),
    },
)
    except stripe.StripeError as exc:
        purchase.delete()

        return HttpResponse(
            f"Stripe checkout error: {exc}",
            status=400,
        )

    purchase.stripe_session_id = checkout_session.id
    purchase.save(update_fields=["stripe_session_id"])

    return redirect(checkout_session.url, code=303)

@login_required
def payment_success(request):
    return render(request, "gallery/payment_success.html")


# gallery/views.py

import stripe

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .emails import send_purchase_download_email
from .models import Purchase


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    signature = request.META.get(
        "HTTP_STRIPE_SIGNATURE",
        "",
    )

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event["type"] in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    }:
        session = event["data"]["object"]

        purchase_id = session.get(
            "metadata",
            {},
        ).get("purchase_id")

        payment_status = session.get("payment_status")

        if purchase_id and payment_status == "paid":
            with transaction.atomic():
                purchase = (
                    Purchase.objects
                    .select_for_update()
                    .select_related(
                        "user",
                        "photo",
                        "photo__album",
                    )
                    .get(pk=purchase_id)
                )

                if purchase.stripe_session_id != session["id"]:
                    return HttpResponse(status=400)

                if purchase.status != "paid":
                    purchase.status = "paid"
                    purchase.paid_at = timezone.now()
                    purchase.save(
                        update_fields=[
                            "status",
                            "paid_at",
                        ]
                    )

                should_send_email = (
                    not purchase.download_email_sent
                )

            if should_send_email:
                try:
                    send_purchase_download_email(purchase)

                    Purchase.objects.filter(
                        pk=purchase.pk,
                        download_email_sent=False,
                    ).update(
                        download_email_sent=True,
                        download_email_sent_at=timezone.now(),
                    )
                except Exception:
                    # Log this in production.
                    # Returning 500 allows Stripe to retry.
                    return HttpResponse(status=500)

    return HttpResponse(status=200)

# gallery/views.py

from django.contrib.admin.views.decorators import staff_member_required

from .forms import MultiplePhotoUploadForm


@staff_member_required
def multiple_photo_upload(request):
    if request.method == "POST":
        form = MultiplePhotoUploadForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            album = form.cleaned_data["album"]
            images = form.cleaned_data["images"]
            is_downloadable = form.cleaned_data[
                "is_downloadable"
            ]
            price_cents = form.cleaned_data[
                "price_cents"
            ]

            created_count = 0

            for uploaded_image in images:
                Photo.objects.create(
                    album=album,
                    title=Path(uploaded_image.name).stem,
                    image=uploaded_image,
                    price_cents=price_cents,
                    is_downloadable=is_downloadable,
                )
                created_count += 1

            messages.success(
                request,
                f"{created_count} photos uploaded.",
            )
            return redirect("dashboard")
    else:
        form = MultiplePhotoUploadForm()

    return render(
        request,
        "gallery/form.html",
        {
            "form": form,
            "title": "Upload multiple photos",
        },
    )

from pathlib import Path

from django.core import signing
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404

from .download_tokens import read_download_token
from .models import DownloadRecord, Purchase


def purchase_download(request, token):
    try:
        purchase_id = read_download_token(
            token,
            max_age_seconds=60 * 60 * 24 * 7,
        )
    except signing.SignatureExpired:
        return HttpResponse(
            "This download link has expired.",
            status=410,
        )
    except signing.BadSignature:
        return HttpResponse(
            "This download link is invalid.",
            status=400,
        )

    purchase = get_object_or_404(
        Purchase.objects.select_related(
            "photo",
            "photo__album",
            "user",
        ),
        pk=purchase_id,
        status="paid",
    )

    photo = purchase.photo

    if not photo.is_downloadable:
        return HttpResponse(
            "Downloads are disabled for this photo.",
            status=403,
        )

    try:
        file_path = Path(photo.image.path)
    except NotImplementedError:
        raise Http404(
            "Direct file streaming is not configured "
            "for remote storage."
        )

    if not file_path.exists():
        raise Http404("The photo file could not be found.")

    DownloadRecord.objects.create(
        user=purchase.user,
        photo=photo,
    )

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=file_path.name,
    )