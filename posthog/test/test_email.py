from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from freezegun import freeze_time

from posthog.email import EmailMessage, _send_email
from posthog.models import MessagingRecord, Organization, Person, Team, User
from posthog.models.instance_setting import override_instance_config
from posthog.test.base import BaseTest


class TestEmail(BaseTest):
    def create_person(self, team: Team, base_distinct_id: str = "") -> Person:
        person = Person.objects.create(team=team)
        person.add_distinct_id(base_distinct_id)
        return person

    @freeze_time("2020-09-21")
    def setUp(self):
        super().setUp()
        self.organization = Organization.objects.create()
        self.team = Team.objects.create(organization=self.organization, name="The Bakery")
        self.user = User.objects.create(email="test@posthog.com")
        self.user2 = User.objects.create(email="test2@posthog.com")
        self.user_red_herring = User.objects.create(email="test+redherring@posthog.com")
        self.organization.members.add(self.user)
        self.organization.members.add(self.user2)
        self.organization.members.add(self.user_red_herring)

        MessagingRecord.objects.get_or_create(
            raw_email="test+redherring@posthog.com",
            campaign_key=f"weekly_report_for_team_{self.team.pk}_on_2020-09-14",
            defaults={"sent_at": timezone.now()},
        )  # This user should not get the emails

    def test_cant_send_emails_if_not_properly_configured(self) -> None:
        with override_instance_config("EMAIL_HOST", None):
            with self.assertRaises(ImproperlyConfigured) as e:
                EmailMessage("test_campaign", "Subject", "template")
            self.assertEqual(str(e.exception), "Email is not enabled in this instance.")

        with override_instance_config("EMAIL_ENABLED", False):
            with self.assertRaises(ImproperlyConfigured) as e:
                EmailMessage("test_campaign", "Subject", "template")
            self.assertEqual(str(e.exception), "Email is not enabled in this instance.")

    def test_cant_send_same_campaign_twice_if_no_resend_frequency(self) -> None:
        with override_instance_config("EMAIL_HOST", "localhost"):
            sent_at = timezone.now()

            record, _ = MessagingRecord.objects.get_or_create(raw_email="test0@posthog.com", campaign_key="campaign_1")
            record.sent_at = sent_at
            record.save()

            with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
                _send_email(
                    campaign_key="campaign_1",
                    to=[{"raw_email": "test0@posthog.com", "recipient": "Test PostHog <test0@posthog.com>"}],
                    subject="Test email",
                    headers={},
                )

            self.assertEqual(len(mail.outbox), 0)

            record.refresh_from_db()
            self.assertEqual(record.sent_at, sent_at)

    # TODO: reinstate this test after https://github.com/PostHog/posthog/pull/17365 is in, ETA 2023-10-21
    #
    # @freeze_time("2020-09-21")
    # def test_can_send_same_campaign_twice_with_resend_frequency(self) -> None:
    #     with override_instance_config("EMAIL_HOST", "localhost"):
    #         sent_at = timezone.now() - timezone.timedelta(days=8)

    #         record = MessagingRecord.objects.create(
    #             raw_email="test0@posthog.com", campaign_key="campaign_2", campaign_count=1
    #         )
    #         record.sent_at = sent_at
    #         record.save()

    #         with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
    #             _send_email(
    #                 campaign_key="campaign_2",
    #                 to=[{"raw_email": "test0@posthog.com", "recipient": "Test PostHog <test0@posthog.com>"}],
    #                 subject="Test email",
    #                 headers={},
    #                 resend_frequency_days=7,
    #             )

    #         self.assertEqual(len(mail.outbox), 1)

    #         record.refresh_from_db()
    #         assert record.sent_at == sent_at

    #         records = (
    #             MessagingRecord.objects.filter(raw_email="test0@posthog.com", campaign_key="campaign_2")
    #             .order_by("-campaign_count")
    #             .all()
    #         )

    #         assert len(records) == 2
    #         assert records[0].campaign_count is None
    #         assert records[1].campaign_count == 1

    @freeze_time("2020-09-21")
    def test_cant_send_same_campaign_twice_less_than_resend_frequency(self) -> None:
        with override_instance_config("EMAIL_HOST", "localhost"):
            sent_at = timezone.now() - timezone.timedelta(days=6)

            record, _ = MessagingRecord.objects.get_or_create(raw_email="test0@posthog.com", campaign_key="campaign_2")
            record.sent_at = sent_at
            record.save()

            with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
                _send_email(
                    campaign_key="campaign_2",
                    to=[{"raw_email": "test0@posthog.com", "recipient": "Test PostHog <test0@posthog.com>"}],
                    subject="Test email",
                    headers={},
                    resend_frequency_days=7,
                )

            self.assertEqual(len(mail.outbox), 0)

            record.refresh_from_db()
            self.assertEqual(record.sent_at, sent_at)

            records = MessagingRecord.objects.filter(raw_email="test0@posthog.com", campaign_key="campaign_2").all()
            assert len(records) == 1

    def test_applies_default_utm_tags(self) -> None:
        with override_instance_config("EMAIL_HOST", "localhost"):
            template = "async_migration_error"
            message = EmailMessage("test_campaign", "Subject", template)

            assert (
                f"https://posthog.com/questions?utm_source=posthog&amp;utm_medium=email&amp;utm_campaign={template}"
                in message.html_body
            )
