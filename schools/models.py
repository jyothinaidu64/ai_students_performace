from django.db import models
from django.utils.text import slugify

class School(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50, blank=True)
    slug = models.SlugField(unique=True, blank=True, help_text="Unique identifier per school (e.g. 'green-valley').")
    is_active = models.BooleanField(default=True)

    # Optional extras for future:
    logo = models.ImageField(upload_to="school_logos/", blank=True, null=True)
    tagline = models.CharField(max_length=255, blank=True)
    primary_color = models.CharField(max_length=20, blank=True, help_text="CSS color (e.g. #2563eb).")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"

    def save(self, *args, **kwargs):
        """Auto-generate unique slug if not provided"""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            # Ensure uniqueness by appending counter if needed
            while School.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
