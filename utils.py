import re

from settings import NAPA_MOTOR_PARTS


def clean_total(text, is_credit_memo=False):
    """
    Cleans the total text by the ff:
    - text is not less than 2
    - text does not start with `.`
    """
    total_txt = re.sub("[^0-9.]", '', text)
    if total_txt == '' or len(total_txt) <= 2 or total_txt.startswith('.') or total_txt.endswith('.'):
        return ''
    elif '.' in total_txt:
        # print('Total', total_txt)
        if is_credit_memo or total_txt.startswith('-'):
            total_txt = f'{total_txt} - REFUND'
        return total_txt
    return ''


def clean_date(text, invoice_type):
    """Cleans the date text and follow the format of `YYYY-MM-DDDD`"""
    if invoice_type == NAPA_MOTOR_PARTS:
        date_txt = re.sub('[^0-9/]', '', text)
        date_txt = date_txt.replace('/', '-')
        strip_txt = date_txt.split('-')
        month, day, year = strip_txt
        if len(strip_txt) == 3 and len(month) == 2 and len(day) == 2 and len(year) == 4:
            if int(month) <= 12 and int(day) <= 31:
                return f'{year}-{month}-{day}'
    else:
        month = text[0].split(' ')[-1]
        if len(month) == 1:
            month = f'0{month}'
        day = text[1]
        if len(day) == 1:
            day = f'0{day}'
        year = text[2].split(' ')[0]
        return f'{year}-{month}-{day}'
    return ''


def clean_po_num(text):
    """Cleans the PO # text"""
    if text and len(text) > 2:
        if text.isalpha():  # Check if all are letters
            return text
        elif text.isalnum():  # Check if it is combination of letters and numbers
            # Check if the 1st two characters are both letter
            first_two = text[:2]
            if not first_two.isalnum():
                return ''
            # Check if the next item after a number is not number flag it as error
            digit_occurred = False
            for item in text:
                if digit_occurred and not item.isdigit():
                    return ''
                if item.isdigit():
                    digit_occurred = True
            po_txt = text[1:]
            if not po_txt.isdigit():
                return po_txt
    return ''


def clean_page(text):
    if text and '/' in text and len(text) == 3 and text[-1].isdigit():
        current_page, last_page = text.split('/')
        if current_page <= last_page:
            return int(last_page)
    return ''