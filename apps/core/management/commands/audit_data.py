"""Data audit / cleanup for the Xinfan Airlines site.

Output is deliberately ASCII-only: the VNC console on the production box
is not UTF-8, so Chinese text renders as mojibake there.

Default run is READ ONLY:

    python manage.py audit_data

Explicit, targeted repairs:

    python manage.py audit_data --delete-request XF102
    python manage.py audit_data --shift-hours 8        # dry run
    python manage.py audit_data --shift-hours 8 --apply
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import ADMIN_ROLES
from apps.flights.models import Flight, FlightCrewSignup, PrivateFlightRequest


def local(value):
    """Render in the site timezone (Asia/Shanghai) to compare with input."""
    if not value:
        return '-'
    return timezone.localtime(value).strftime('%Y-%m-%d %H:%M')


class Command(BaseCommand):
    help = 'Read-only audit of flight/request times and account permissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-request',
            metavar='FLIGHT_NUMBER',
            help='Delete every private flight request with this flight number',
        )
        parser.add_argument(
            '--shift-hours',
            type=int,
            metavar='N',
            help='Shift flight/request times by N hours (negative to subtract). '
                 'Dry run unless --apply is also given.',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually perform the --shift-hours change',
        )

    def handle(self, *args, **options):
        if options.get('delete_request'):
            self.delete_request(options['delete_request'])
            self.stdout.write('')

        if options.get('shift_hours'):
            self.shift_times(options['shift_hours'], options['apply'])
            self.stdout.write('')

        self.audit()

    # ── actions ────────────────────────────────────────

    def delete_request(self, flight_number):
        qs = PrivateFlightRequest.objects.filter(flight_number=flight_number)
        found = list(qs)
        if not found:
            self.stdout.write('DELETE: no request with flight_number=%s' % flight_number)
            return

        for r in found:
            self.stdout.write('DELETE target: %s | %s | %s -> %s | %s | submitted %s' % (
                r.flight_number, r.user.username,
                local(r.departure_time), local(r.arrival_time),
                r.status, local(r.created_at)))

        # Detach the generated flight first, then delete, in one transaction.
        with transaction.atomic():
            for r in found:
                if r.created_flight_id:
                    flight = r.created_flight
                    r.created_flight = None
                    r.save(update_fields=['created_flight'])
                    self.stdout.write('  detached flight %s' % flight.flight_number)
                    flight.delete()
                r.delete()
        self.stdout.write('DELETE: removed %d request(s)' % len(found))

    def shift_times(self, hours, apply_change):
        from datetime import timedelta

        delta = timedelta(hours=hours)
        flights = list(Flight.objects.all())
        requests = list(PrivateFlightRequest.objects.all())

        self.stdout.write('SHIFT: %+d hour(s) requested' % hours)
        self.stdout.write('SHIFT: %d flight(s), %d request(s) affected' % (
            len(flights), len(requests)))

        for f in flights:
            self.stdout.write('  %s: %s -> %s | %s -> %s' % (
                f.flight_number, local(f.departure_time),
                local(f.departure_time + delta),
                local(f.arrival_time), local(f.arrival_time + delta)))
        for r in requests:
            self.stdout.write('  %s: %s -> %s | %s -> %s' % (
                r.flight_number, local(r.departure_time),
                local(r.departure_time + delta),
                local(r.arrival_time), local(r.arrival_time + delta)))

        if not apply_change:
            self.stdout.write('SHIFT: DRY RUN - nothing changed. Re-run with --apply')
            return

        with transaction.atomic():
            for f in flights:
                f.departure_time = f.departure_time + delta
                f.arrival_time = f.arrival_time + delta
                f.save(update_fields=['departure_time', 'arrival_time'])
            for r in requests:
                r.departure_time = r.departure_time + delta
                r.arrival_time = r.arrival_time + delta
                r.save(update_fields=['departure_time', 'arrival_time'])
        self.stdout.write('SHIFT: APPLIED to %d flight(s) and %d request(s)' % (
            len(flights), len(requests)))

    # ── report ─────────────────────────────────────────

    def audit(self):
        say = self.stdout.write
        flights = list(Flight.objects.all())
        requests = list(PrivateFlightRequest.objects.all())

        say('== FLIGHTS ==  (times shown in %s)' % timezone.get_current_timezone())
        say('flights  : %d' % len(flights))
        say('requests : %d' % len(requests))
        say('signups  : %d' % FlightCrewSignup.objects.count())
        say('')

        if flights:
            for f in flights[:20]:
                say('%s | %s -> %s | %s' % (
                    f.flight_number, local(f.departure_time),
                    local(f.arrival_time), f.status))
        else:
            say('(no flights)')
        say('')

        if requests:
            say('-- private flight requests --')
            for r in requests[:20]:
                say('%s | %s | dep %s -> arr %s | %s | submitted %s' % (
                    r.flight_number, r.user.username,
                    local(r.departure_time), local(r.arrival_time),
                    r.status, local(r.created_at)))
        else:
            say('(no private flight requests)')
        say('')

        say('== ACCOUNTS ==')
        say('total users: %d' % User.objects.count())
        say('')

        say('-- can log into /admin/ (is_staff=True) --')
        staff = list(User.objects.filter(is_staff=True))
        if staff:
            for u in staff:
                role = getattr(getattr(u, 'profile', None), 'role', 'MISSING')
                say('%-20s role=%-18s superuser=%s' % (u.username, role, u.is_superuser))
        else:
            say('(none)')
        say('')

        say('-- can change other users roles (role in ADMIN_ROLES) --')
        privileged = list(User.objects.filter(profile__role__in=sorted(ADMIN_ROLES)))
        say('count: %d' % len(privileged))
        for u in privileged:
            say('%-20s role=%s' % (u.username, u.profile.role))
        say('')

        say('== AUDIT COMPLETE ==')
