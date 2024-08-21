import time
from datetime import datetime, timedelta
from pytz import timezone

def get_timestamp(hoursLater):
    currentTime = time.time()
    secLater = hoursLater*60*60
    timestamp = currentTime + secLater

    return timestamp

def end_of_day():
    neopetsTimezone = timezone('America/Vancouver')
    neopetsCurrentTime = datetime.now(neopetsTimezone)
    midnight = datetime.now(neopetsTimezone).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=24)

    return time.time() + (midnight-neopetsCurrentTime).total_seconds()

def end_of_hour():
    neopetsTimezone = timezone('America/Vancouver')
    neopetsCurrentTime = datetime.now(neopetsTimezone)
    hour = (datetime.now(neopetsTimezone)+ timedelta(hours=1)).replace(minute=4, second=0, microsecond=0)

    return time.time() + (hour-neopetsCurrentTime).total_seconds()

def time_remaining(clock):
    min_remaning = (clock - time.time())/60
    return int(min_remaning)
