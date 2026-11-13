from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils import timezone

from orders.models import Order
from orders.inventory import restore_order_inventory
from orders.payments import RazorpayError, fetch_razorpay_order_payments


class Command(BaseCommand):
    help = "Expire abandoned online orders and safely release their reserved inventory."

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=getattr(settings, "PENDING_PAYMENT_EXPIRY_MINUTES", 30),
            help="Minimum age of an unpaid order before expiry (default: 30).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report eligible orders without changing orders or inventory.",
        )

    def handle(self, *args, **options):
        minutes = options["minutes"]
        if minutes < 1:
            self.stderr.write(self.style.ERROR("--minutes must be at least 1."))
            return

        cutoff = timezone.now() - timedelta(minutes=minutes)
        candidates = Order.objects.filter(
            status="pending_payment",
            payment_status="Pending - Razorpay",
            created_at__lte=cutoff,
        ).exclude(razorpay_order_id="").order_by("created_at")

        checked = expired = paid = review = skipped = 0
        for candidate in candidates.iterator():
            checked += 1
            try:
                attempts = fetch_razorpay_order_payments(candidate.razorpay_order_id)
            except RazorpayError as exc:
                skipped += 1
                self.stderr.write(self.style.WARNING(
                    f"{candidate.order_number}: provider check failed; left untouched ({exc})"
                ))
                continue

            captured = next((p for p in attempts if p.get("status") == "captured"), None)
            in_flight = any(p.get("status") in {"created", "authorized", "pending"} for p in attempts)

            if captured:
                payment_id = captured.get("id")
                try:
                    with transaction.atomic():
                        order = Order.objects.select_for_update().get(pk=candidate.pk)
                        if order.status != "pending_payment" or order.payment_status != "Pending - Razorpay":
                            skipped += 1
                            continue
                        if int(captured.get("amount", -1)) != int(order.total * 100) or captured.get("currency") != "INR" or not payment_id:
                            order.status = "payment_review"
                            order.payment_status = "Payment Captured - Review Required"
                            order.save(update_fields=["status", "payment_status", "updated_at"])
                            review += 1
                            continue
                        order.razorpay_payment_id = payment_id
                        order.payment_status = "Paid"
                        order.status = "placed"
                        order.save(update_fields=["razorpay_payment_id", "payment_status", "status", "updated_at"])
                        paid += 1
                except IntegrityError:
                    skipped += 1
                continue

            if in_flight:
                skipped += 1
                continue

            if options["dry_run"]:
                self.stdout.write(f"Would expire {candidate.order_number} and release its inventory.")
                expired += 1
                continue

            with transaction.atomic():
                order = Order.objects.select_for_update().get(pk=candidate.pk)
                if order.status != "pending_payment" or order.payment_status != "Pending - Razorpay" or order.created_at > cutoff:
                    skipped += 1
                    continue
                restore_order_inventory(order)
                order.status = "cancelled"
                order.payment_status = "Expired - Unpaid"
                order.save(update_fields=["status", "payment_status", "updated_at"])
                expired += 1

        self.stdout.write(self.style.SUCCESS(
            f"Checked {checked}; expired {expired}; reconciled paid {paid}; flagged for review {review}; skipped {skipped}."
        ))
