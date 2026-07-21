from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class SiteSettings(models.Model):
    site_name=models.CharField(max_length=120,default='Event Photo Gallery')
    hero_title=models.CharField(max_length=180,default='Relive the Moment')
    hero_subtitle=models.CharField(max_length=300,default='Browse albums and download your favorite photos.')
    hero_image=models.ImageField(upload_to='site/',blank=True,null=True)
    footer_text=models.CharField(max_length=240,default='© Event Photo Gallery')
    class Meta: verbose_name_plural='Site settings'
    def __str__(self): return self.site_name

class Album(models.Model):
    title=models.CharField(max_length=150)
    slug=models.SlugField(unique=True)
    description=models.TextField(blank=True)
    cover=models.ImageField(upload_to='covers/',blank=True,null=True)
    is_published=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']
    def __str__(self): return self.title
    def get_absolute_url(self): return reverse('album_detail',args=[self.slug])

class Photo(models.Model):
    album = models.ForeignKey(
        "Album",
        related_name="photos",
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to="photos/")
    price_cents = models.PositiveIntegerField(default=500)
    is_downloadable = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def price_display(self):
        return self.price_cents / 100

class DownloadRecord(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    photo=models.ForeignKey(Photo,on_delete=models.CASCADE)
    downloaded_at=models.DateTimeField(auto_now_add=True)

class Purchase(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    stripe_session_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.photo} - {self.status}"