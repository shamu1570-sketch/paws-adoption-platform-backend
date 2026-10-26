from typing import Annotated

from fastapi import Depends

from src.core.config import settings
from src.notifications.gmail import DisabledEmailSender, GmailEmailSender
from src.notifications.interfaces import EmailSender
from src.notifications.invitation import InvitationNotifier
from src.notifications.status import StatusNotifier
from src.notifications.tracking import TrackingNotifier


def get_email_sender() -> EmailSender:
    if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
        return GmailEmailSender(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            from_name=settings.EMAIL_FROM_NAME,
        )
    return DisabledEmailSender()


def get_tracking_notifier(
    sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> TrackingNotifier:
    return TrackingNotifier(sender, settings.FRONTEND_URL, settings.APP_NAME)


TrackingNotifierDep = Annotated[TrackingNotifier, Depends(get_tracking_notifier)]


def get_status_notifier(
    sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> StatusNotifier:
    return StatusNotifier(sender, settings.FRONTEND_URL, settings.APP_NAME)


StatusNotifierDep = Annotated[StatusNotifier, Depends(get_status_notifier)]


def get_invitation_notifier(
    sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> InvitationNotifier:
    return InvitationNotifier(sender, settings.FRONTEND_URL, settings.APP_NAME)


InvitationNotifierDep = Annotated[InvitationNotifier, Depends(get_invitation_notifier)]
