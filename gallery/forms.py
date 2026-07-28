from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Album,Photo,SiteSettings
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
    class Meta: model=Photo; fields=('album','title','image','is_downloadable')
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
    price_cents = forms.IntegerField(
        min_value=50,
        initial=500,
        help_text="500 means $5.00"
    )

