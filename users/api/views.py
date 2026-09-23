import logging

from rest_framework import generics, status
from rest_framework.response import Response

from users.models import WaitlistEntry
from users.services.email_service import send_waitlist_emails

from .serializers import WaitlistEntrySerializer

logger = logging.getLogger(__name__)

SUCCESS_MESSAGE = "You're on the waitlist! We'll be in touch soon."
SUCCESS_MESSAGE_EMAILED = "You're on the waitlist! Check your inbox for a confirmation email."


class WaitlistListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/waitlist  -> {"success": true, "count": N, "data": [...]}
    POST /api/waitlist  -> {"message": "..."} (201) or {"error": "..."} (400/409/500)

    Mirrors the response contract of the original Node/Express + SQLite
    implementation so the existing frontend JavaScript keeps working unchanged.
    """
    queryset = WaitlistEntry.objects.all()
    serializer_class = WaitlistEntrySerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        role = request.data.get('role')

        if not email or not role:
            return Response(
                {'error': 'Email and role are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if WaitlistEntry.objects.filter(email__iexact=email).exists():
            return Response(
                {'error': 'This email is already on the waitlist.'},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'An error occurred while saving your submission.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        entry = serializer.save()
        logger.info('Waitlist signup created: id=%s role=%s.', entry.pk, entry.role)

        # The entry is committed at this point; email problems are logged by
        # the service and never turn a successful signup into an error.
        sent = send_waitlist_emails(entry)
        return Response(
            {'message': SUCCESS_MESSAGE_EMAILED if sent['subscriber'] else SUCCESS_MESSAGE},
            status=status.HTTP_201_CREATED,
        )
