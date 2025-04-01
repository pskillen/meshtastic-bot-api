from datetime import datetime, timezone

from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse

from django_jinja import library
from jinja2 import Environment


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
        'now': datetime.now,  # Add current timestamp function
        'utcnow': lambda: datetime.now(timezone.utc),  # Add UTC timestamp function
    })
    
    # Add some common filters
    env.filters.update({
        'datetime': datetime.fromtimestamp,
        'isoformat': lambda dt: dt.isoformat() if dt else '',
        'round': lambda value, n=None: '---' if value is None else round(value, n) if n is not None else round(value),
    })
    
    return env


@library.filter(name='timesince')
def time_since_date(last_heard_timestamp):
    if last_heard_timestamp is None:
        return "Never"
    if not isinstance(last_heard_timestamp, datetime):
        last_heard = datetime.fromtimestamp(last_heard_timestamp, timezone.utc)
    else:
        last_heard = last_heard_timestamp

    now = datetime.now(timezone.utc)
    delta = now - last_heard

    if delta.total_seconds() < 0:
        return "0s ago"

    if delta.days > 0:
        return f"{delta.days}d ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours}h ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes}m ago"
    else:
        return f"{delta.seconds}s ago"


@library.filter(name='seconds_human_readable')
def seconds_human_readable(seconds):
    if seconds is None or seconds < 0:
        return "0s"

    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"
