import datetime
from calendar import monthrange



def truncate(n, decimals=0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def find_string_between_strings(string, first, last):
    try:
        start = string.index(first) + len(first)
        end = string.index(last, start)
        return string[start:end]
    except ValueError:
        return ' '

def get_current_date(current=True):
    now = datetime.date.today()
    year = now.year
    month = now.month
    if not current:
        month = month - 1
    _, last_day_in_month = monthrange(year, month)
    return year, month, last_day_in_month

def nslookup(dns):
    import socket
    return socket.gethostbyname(dns)