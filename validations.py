import re


def valid_total_value(text):
    """
    Validates the total text by the ff:
    - text is not less than 2
    - text does not start with `.`
    """
    total_txt = re.sub("[^0-9.]", '', text)
    if total_txt == '' or len(total_txt) <= 2 or total_txt.startswith('.') or total_txt.endswith('.'):
        return ''
    elif '.' in total_txt:
        # print('Total', total_txt)
        return total_txt
    return ''


def valid_date_value(text):
    """Validates the date cleaned text has the format of `MM-DD-YYYY`"""
    date_txt = re.sub('[^0-9/]', '', text)
    date_txt = date_txt.replace('/', '-')
    strip_txt = date_txt.split('-')
    if len(strip_txt) == 3 and len(strip_txt[0]) == 2 and len(strip_txt[1]) == 2 and len(strip_txt[2]) == 4 \
            and int(strip_txt[0]) <= 12 and int(strip_txt[1]) <= 31:
        return date_txt
    return ''


def valid_po_num_value(text):
    """Validates PO# text"""
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


def valid_page_value(text):
    if text and '/' in text and len(text) == 3 and text[-1].isdigit():
        current_page, last_page = text.split('/')
        if current_page <= last_page:
            return int(last_page)
    return ''