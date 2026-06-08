from datetime import datetime, timezone, timedelta


def utc_now() -> datetime:
    # GMT-6 (UTC-6) - Zona horaria de México Centro
    gmt_minus_6 = timezone(timedelta(hours=-6))
    return datetime.now(gmt_minus_6)


def utc_today_date():
    return utc_now().date()
