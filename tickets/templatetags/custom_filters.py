from django import template
from datetime import datetime
from datetime import timedelta

register = template.Library()


@register.filter
def dynamic_zfill(ticket_id, store_code):
    """
    Format the ticket ID with leading zeros, including the business year (April 1 to March 31),
    store code, and the dynamic portion.
    """
    ticket_id_str = str(ticket_id)
    zeros_count = max(6 - len(ticket_id_str), 0)
    
    # Determine the business year based on the current date
    today = datetime.now()
    if today.month >= 4:  # If the current date is on or after April
        current_year = today.year % 100
        next_year = (today.year + 1) % 100
    else:  # If the current date is before April
        current_year = (today.year - 1) % 100
        next_year = today.year % 100
    
    # Return the formatted CFA code
    return f'{store_code}{current_year:02}{next_year:02}{ticket_id_str.zfill(zeros_count + len(ticket_id_str))}'


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def ticket_ageing(created_date, closed_date):
    """
    Returns the difference in days between created_date and closed_date.
    If closed_date is None, it uses the current date.
    Handles both datetime and date types.
    """
    if created_date:
        # Ensure created_date is a date object (either from datetime or already a date)
        if isinstance(created_date, datetime):
            created_date = created_date.date()
        
        # Ensure closed_date is a date object, if closed_date is None, use the current date
        if closed_date:
            if isinstance(closed_date, datetime):
                closed_date = closed_date.date()
        else:
            closed_date = datetime.now().date()

        # Calculate the difference in days
        return (closed_date - created_date).days

    return "N/A"