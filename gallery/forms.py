from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Album,Photo,SiteSettings
from decimal import Decimal

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
        )
class AlbumForm(forms.ModelForm):
    class Meta: model=Album; fields=('title','slug','description','cover','is_published')
class PhotoForm(forms.ModelForm):
    price = forms.DecimalField(
        label="Price ($)",
        max_digits=8,
        decimal_places=2,
        initial=5.00,
        min_value=Decimal("0.50"),
    )

    class Meta:
        model = Photo
        fields = (
            "album",
            "title",
            "image",
            "price",
            "is_downloadable",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields["price"].initial = (
                Decimal(self.instance.price_cents) / 100
            )

    def save(self, commit=True):
        photo = super().save(commit=False)

        photo.price_cents = int(
            self.cleaned_data["price"] * 100
        )

        if commit:
            photo.save()

        return photo
class SiteSettingsForm(forms.ModelForm):
    class Meta: model=SiteSettings; fields=('site_name','hero_title','hero_subtitle','hero_image','footer_text')
# gallery/forms.py

from django import forms
from PIL import Image

from .models import Album


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):
            return [
                single_file_clean(file, initial)
                for file in data
            ]

        return [single_file_clean(data, initial)]


class MultiplePhotoUploadForm(forms.Form):
    album = forms.ModelChoiceField(
        queryset=Album.objects.all()
    )
    images = MultipleImageField()
    is_downloadable = forms.BooleanField(
        required=False,
        initial=True
    )
    price = forms.DecimalField(
    label="Price ($)",
    max_digits=8,
    decimal_places=2,
    min_value=Decimal("0.50"),
    initial=Decimal("5.00"),
)

