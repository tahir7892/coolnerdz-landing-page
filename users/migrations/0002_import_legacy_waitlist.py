from datetime import datetime, timezone

from django.db import migrations

LEGACY_TABLE = 'waitlist'


def import_legacy_waitlist(apps, schema_editor):
    """
    Copy rows from the table written by the old Node/Express app into
    users_waitlistentry. The legacy table is left untouched, and rows whose
    email already exists are skipped, so this is safe to run more than once.
    """
    connection = schema_editor.connection
    if LEGACY_TABLE not in connection.introspection.table_names():
        return

    WaitlistEntry = apps.get_model('users', 'WaitlistEntry')
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT id, email, role, created_at FROM {LEGACY_TABLE} ORDER BY id')
        rows = cursor.fetchall()

    for legacy_id, email, role, created_at in rows:
        if WaitlistEntry.objects.filter(email__iexact=email).exists():
            continue
        # SQLite CURRENT_TIMESTAMP values are naive UTC; the driver may return
        # them as datetime (DATETIME column) or as 'YYYY-MM-DD HH:MM:SS' text.
        if isinstance(created_at, str):
            created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        created = created_at.replace(tzinfo=timezone.utc)
        entry = WaitlistEntry.objects.create(id=legacy_id, email=email, role=role)
        # created_at is auto_now_add, so set the original timestamp afterwards.
        WaitlistEntry.objects.filter(pk=entry.pk).update(created_at=created)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(import_legacy_waitlist, migrations.RunPython.noop),
    ]
