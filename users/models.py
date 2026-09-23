from django.db import models


class WaitlistEntry(models.Model):
    ROLE_CHOICES = [
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
        ('Athlete', 'Athlete'),
        ('Counselor', 'Counselor'),
        ('Organization', 'Organization'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.email} ({self.role})'
