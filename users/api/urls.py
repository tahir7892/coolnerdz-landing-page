from django.urls import path

from .views import WaitlistListCreateAPIView

app_name = 'users_api'

urlpatterns = [
    path('waitlist', WaitlistListCreateAPIView.as_view(), name='waitlist'),
]
