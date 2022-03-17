import os
import shutil
import re
import cv2
import numpy as np

from PyPDF2 import PdfFileReader, PdfFileWriter
from pytesseract import pytesseract
from pdf2image import convert_from_path
from settings import *


def valid_total_value(text):
    """
    Validates the total cleaned text by the ff:
    - text is not less than 2
    - text does not start with `.`
    """
    cleaned_total_txt = re.sub("[^0-9.]", '', text)
    if cleaned_total_txt == '' or len(cleaned_total_txt) <= 2 or cleaned_total_txt.startswith('.'):
        return None
    elif '.' in cleaned_total_txt:
        print('Total', cleaned_total_txt)
        return cleaned_total_txt
    return None


def valid_date_value(text):
    """Validates the date cleaned text has the format of `MM-DD-YYYY`"""
    cleaned_date_txt = re.sub('[^0-9/]', '', text)
    cleaned_date_txt = cleaned_date_txt.replace('/', '-')
    strip_text = cleaned_date_txt.split('-')
    if len(strip_text) == 3 and len(strip_text[0]) == 2 and len(strip_text[1]) == 2 and len(strip_text[2]) == 4 \
            and int(strip_text[0]) <= 12 and int(strip_text[1]) <= 31:
        return cleaned_date_txt
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
            return text[1:]
    return ''


def valid_page_value(text):
    if text and '/' in text and len(text) == 3 and text[-1].isdigit():
        split_text = text.split('/')
        if split_text[0] == split_text[-1]:
            return int(split_text[-1])
    return ''


def modify_image(img, additional_black_threshold, retry_count):
    if retry_count == 3:
        img = cv2.erode(img, np.ones((1, 1), np.uint8))
    elif retry_count == 1:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.threshold(img, 160 + additional_black_threshold, 255, cv2.THRESH_BINARY)[1]
        img = cv2.erode(img, np.ones((2, 2), np.uint8))
    else:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.threshold(img, 160 + additional_black_threshold, 255, cv2.THRESH_BINARY)[1]
        # img = cv2.erode(img, np.ones((1, 1), np.uint8))
    return img


def extract_text(img):
    # img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    pytesseract.tesseract_cmd = PATH_TO_TESSERACT
    cv2.imshow('pic', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return pytesseract.image_to_string(img, config=r'--oem 3')


def get_file_name(image_path):
    po_identifier = 'PO#:'
    date_identifier = 'Date:'
    total_identifiers = ['Credit Memo', 'Charge Sale', 'Subtotal', 'Total']
    page_identifier = 'Page:'

    img = cv2.imread(image_path)
    retry_max = 5
    retry_count = 1
    additional_black_threshold = 0
    while True:
        modified_img = modify_image(img, additional_black_threshold, retry_count)
        texts = extract_text(modified_img)
        po_txt, date_txt, total_txt, page_txt = '', '', '', ''
        prev_txt_total = False

        for text in texts.split('\n'):
            if not total_txt:
                # if prev_txt_total:
                #     prev_txt_total = False
                #     cleaned_total_txt = valid_total_value(text)
                #     if cleaned_total_txt is not None:
                #         total_txt = cleaned_total_txt
                #         continue
                # else:
                for tot_identifier in total_identifiers:
                    if tot_identifier in text:
                        cleaned_total_txt = valid_total_value(text)
                        if cleaned_total_txt is not None:
                            total_txt = cleaned_total_txt
                            break

            # if text.strip() == 'Total':
            #     prev_txt_total = True
            #     continue

            if po_identifier in text and not po_txt:
                po_txt = text.replace(po_identifier, '').strip()
                po_txt = valid_po_num_value(po_txt)
                print('PO', po_txt)
                continue
            if date_identifier in text and not date_txt:
                date_txt = text.replace(date_identifier, '').strip()
                date_txt = valid_date_value(date_txt)
                print('Date', date_txt)
                continue
            if page_identifier in text and not page_txt:
                page_txt = text.replace(page_identifier, '').strip()
                page_txt = valid_page_value(page_txt)
                print('Page', page_txt)
                continue

        if po_txt and total_txt and date_txt and page_txt:
            total_txt = f'${total_txt}'
            return page_txt, True, f'{po_txt} - {date_txt} - {total_txt}'
        elif retry_count == retry_max:
            total_txt = os.path.basename(image_path).replace('.jpg', '')
            return page_txt, False, f'{po_txt} - {date_txt} - {total_txt}'
        else:
            additional_black_threshold += 8
            retry_count += 1


def convert_pdf_to_image(pdf_file_path, image_path):
    images = convert_from_path(pdf_file_path, poppler_path=POPPLER_PATH)
    if len(images) > 1:
        raise ValueError('Multiple image found on the PDF document.')

    image = images[0]
    image_file_name = os.path.basename(pdf_file_path).replace('pdf', 'jpg')
    image_file_path = os.path.join(image_path, image_file_name)
    image.save(image_file_path, 'JPEG')

    return image_file_path


def split_pdf(file_path, store_path, signals):
    if not file_path.endswith('.pdf'):
        raise ValueError('Invalid file extension.')

    main_pdf_filename = os.path.basename(file_path).replace('.pdf', '')
    main_pdf_path = os.path.join(store_path, main_pdf_filename)
    image_path = os.path.join(main_pdf_path, 'images')
    error_named_path = os.path.join(main_pdf_path, 'error_named_files')
    os.makedirs(main_pdf_path, exist_ok=True)
    os.makedirs(image_path, exist_ok=True)

    main_pdf = PdfFileReader(open(file_path, 'rb'))
    multi_page_scope = 0
    for i in range(main_pdf.numPages):
        output = PdfFileWriter()
        output.addPage(main_pdf.getPage(i))
        page_num = i + 1

        if multi_page_scope != 0 and multi_page_scope < i:
            continue

        initial_file_name = f'page{page_num}.pdf'
        pdf_file_path = os.path.join(main_pdf_path, initial_file_name)
        with open(pdf_file_path, 'wb') as out:
            output.write(out)

        image_file_path = convert_pdf_to_image(pdf_file_path, image_path)
        page_count, success, pdf_file_name = get_file_name(image_file_path)

        # Check if the current page contains multiple pages
        if page_count and page_count > 1:
            if multi_page_scope < i:
                multi_page_scope = i + page_count
                continue

        # Set to 0 if page count is only 1 or the index already hit the last page
        multi_page_scope = 0

        if success:
            move_dir = os.path.join(main_pdf_path, f'{pdf_file_name}.pdf')
        else:
            os.makedirs(error_named_path, exist_ok=True)
            move_dir = os.path.join(error_named_path, f'{pdf_file_name}.pdf')

        print(move_dir)
        # Remove the file if it exist
        if os.path.exists(move_dir):
            os.remove(move_dir)
        os.rename(pdf_file_path, move_dir)
        signals.signal_str.emit(f'{page_num} out of {main_pdf.numPages} in {main_pdf_filename}.pdf')

    shutil.rmtree(image_path)
