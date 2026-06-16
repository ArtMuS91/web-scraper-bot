from datetime import date


UA_MONTHS = {
    "січня": 1, "лютого": 2, "березня": 3, "квітня": 4,
    "травня": 5, "червня": 6, "липня": 7, "серпня": 8,
    "вересня": 9, "жовтня": 10, "листопада": 11, "грудня": 12,
}


def parse_ua_date(text: str) -> date:
    parts = text.strip().split()
    if len(parts) == 2:
        day, month_name = parts
        month = UA_MONTHS.get(month_name.lower())
        if month:
            year = date.today().year
            d = date(year, month, int(day))
            # if date is in future, it belongs to previous year
            if d > date.today():
                d = date(year - 1, month, int(day))
            return d
    return date.min
