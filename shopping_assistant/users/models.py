from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(
        max_length=15,
        blank=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', message="Phone number must be valid.")]
    )
    shipping_address = models.JSONField(default=dict)  # e.g., {"street": "", "city": "", "zip": ""}
    billing_address = models.JSONField(default=dict, blank=True)
    preferences = models.JSONField(default=dict, blank=True)  # e.g., {"preferred_sizes": ["M", "L"]}
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"