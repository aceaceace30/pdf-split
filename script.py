import shutil
import cv2
import numpy as np

from PyPDF2 import PdfFileReader, PdfFileWriter
from pytesseract import pytesseract, Output
from pdf2image import convert_from_path
from settings import *
from validations import (
    valid_total_value, valid_date_value, valid_po_num_value, valid_page_value
)


def modify_image(img, additional_black_threshold, retry_count):
    if retry_count == 2:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.erode(img, np.ones((1, 1), np.uint8))
    elif retry_count > 2:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Remove shadows, cf. https://stackoverflow.com/a/44752405/11089932
        dilated_img = cv2.dilate(img, np.ones((7, 7), np.uint8))
        bg_img = cv2.medianBlur(dilated_img, 21)
        img = 255 - cv2.absdiff(img, bg_img)
        img = cv2.normalize(img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        img = cv2.threshold(img, 140 + additional_black_threshold, 255, cv2.THRESH_BINARY)[1]
    return img


def extract_text(img, invoice_type):
    # cv2.imshow('pic', img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    pytesseract.tesseract_cmd = PATH_TO_TESSERACT
    if invoice_type == NAPA_MOTOR_PARTS:
        return pytesseract.image_to_data(img, config=r'--oem 1', output_type=Output.DICT)['text']
    return pytesseract.image_to_string(img, config=r'--oem 1')


def get_file_name(invoice_type, image_path):
    po_identifier = 'PO#:'
    date_identifier = 'Date:'
    total_identifiers = ['Memo', 'Sale', 'Subtotal', 'Total']
    page_identifier = 'Page:'
    identifiers = [po_identifier, date_identifier, page_identifier] + total_identifiers

    img = cv2.imread(image_path)
    retry_max = 3

    if invoice_type == NAPA_MOTOR_PARTS:
        retry_max = 10
        width, height = (2550, 3300)
        img = cv2.resize(img, (width, height))

    retry_count = 1
    additional_black_threshold = 0
    po_txt, date_txt, total_txt, last_page_txt = '', '', '', ''
    while True:
        modified_img = modify_image(img, additional_black_threshold, retry_count)
        extracted_text = extract_text(modified_img, invoice_type)
        if invoice_type == NAPA_MOTOR_PARTS:
            texts = list()
            for idx, t in enumerate(extracted_text):
                strip_text = t.strip()
                if strip_text and strip_text in identifiers:
                    try:
                        next_text = extracted_text[idx+1].strip()
                    except IndexError:
                        next_text = ''
                    combined_text = f'{strip_text + next_text}'
                    if combined_text not in texts and next_text:
                        texts.append(combined_text)
            if len(texts) >= 4:
                for text in texts:
                    if page_identifier in text and not last_page_txt:
                        last_page_txt = valid_page_value(text.replace(page_identifier, ''))
                    elif po_identifier in text and not po_txt:
                        po_txt = valid_po_num_value(text.replace(po_identifier, ''))
                    elif date_identifier in text and not date_txt:
                        date_txt = valid_date_value(text.replace(date_identifier, ''))
                    else:
                        for identifier in total_identifiers:
                            if identifier in text and not total_txt:
                                total_txt = valid_total_value(text)
                                break
        else:
            texts = extracted_text.split("\n")
            for idx, text in enumerate(texts):
                if not text:
                    continue
                # print(idx, text)
                split_text = text.split('/')
                if "Cust. PO#" in text and not po_txt:
                    po_txt = valid_po_num_value(texts[idx+4])
                    if not po_txt:
                        for i in range(1, 3):
                            try:
                                next_text = texts[idx+i]
                                if next_text.replace(' ', '').isalpha():
                                    po_txt = next_text
                                else:
                                    po_txt = next_text.split(' ')[-2]
                                    if po_txt:
                                        po_txt = valid_po_num_value(po_txt)
                                break
                            except IndexError:
                                continue
                elif idx <= 45 and len(split_text) == 3 and not date_txt:
                    month = split_text[0].split(' ')[-1]
                    day = split_text[1]
                    year = split_text[2].split(' ')[0]
                    date_txt = f'{month}-{day}-{year}'
                    # date_txt = text.replace('/', '-')
                elif "INVOICE TOTAL" in text and not total_txt:
                    total_txt = valid_total_value(text)

        print(f'Retry: {retry_count}/{retry_max}', 'Details:', po_txt, date_txt, total_txt, last_page_txt)
        print('------------------------------------------------------')
        if po_txt and date_txt and total_txt:
            total_txt = f'${total_txt}'
            return True, 1, f'{po_txt} - {date_txt} - {total_txt}'
        elif retry_count == retry_max:
            return False, last_page_txt, f'{po_txt} - {date_txt} - {total_txt}'
        else:
            additional_black_threshold += 10
            retry_count += 1


def convert_pdf_to_image(pdf_file_path, image_path):
    images = convert_from_path(pdf_file_path, poppler_path=POPPLER_PATH)
    image = images[-1]  # Always get the last page for pdf that has multiple page
    image_file_name = os.path.basename(pdf_file_path).replace('pdf', 'jpg')
    image_file_path = os.path.join(image_path, image_file_name)
    image.save(image_file_path, 'JPEG')

    return image_file_path


def split_pdf(invoice_type, file_path, store_path, signals):
    if not file_path.endswith('.pdf'):
        raise ValueError('Invalid file extension.')

    main_pdf_filename = os.path.basename(file_path).replace('.pdf', '')
    main_pdf_path = os.path.join(store_path, main_pdf_filename)
    image_path = os.path.join(main_pdf_path, 'images')
    error_named_path = os.path.join(main_pdf_path, 'error_named_files')
    correct_named_path = os.path.join(main_pdf_path, 'correct_named_files')
    holder_folder_path = os.path.join(main_pdf_path, 'you_can_delete_this_folder')
    os.makedirs(main_pdf_path, exist_ok=True)
    os.makedirs(image_path, exist_ok=True)
    os.makedirs(holder_folder_path, exist_ok=True)

    main_pdf = PdfFileReader(open(file_path, 'rb'))
    multi_page_scope = 0
    multi_page_idx = list()
    for i in range(main_pdf.numPages):
        page_num = i + 1
        output = PdfFileWriter()
        # check if the current page is the last page of multiple page and combine the previous pdf
        if multi_page_scope == i and multi_page_idx:
            for item in multi_page_idx:
                included_pdf = os.path.join(holder_folder_path, f'page{item+1}.pdf')
                multi_pdf = PdfFileReader(open(included_pdf, 'rb'))
                output.addPage(multi_pdf.getPage(0))
        output.addPage(main_pdf.getPage(i))

        # Skip if this page is not the last page of the multiple pages
        # if multi_page_scope != 0 and multi_page_scope < i:
        #     continue

        initial_file_name = f'page{page_num}.pdf'
        pdf_file_path = os.path.join(holder_folder_path, initial_file_name)
        with open(pdf_file_path, 'wb') as out:
            output.write(out)

        image_file_path = convert_pdf_to_image(pdf_file_path, image_path)
        is_success, page_count, pdf_file_name = get_file_name(invoice_type, image_file_path)

        # Check if the current page contains multiple pages
        if page_count and page_count > 1:
            if multi_page_scope < i:
                multi_page_scope = i + page_count - 1
                multi_page_idx.append(i)
                continue

        # Set to 0 if page count is only 1 or the index already hit the last page of multiple page
        multi_page_scope = 0
        multi_page_idx = list()

        if is_success:
            os.makedirs(correct_named_path, exist_ok=True)
            move_dir = os.path.join(correct_named_path, f'{pdf_file_name}.pdf')
        else:
            os.makedirs(error_named_path, exist_ok=True)
            move_dir = os.path.join(error_named_path, f'{pdf_file_name}.pdf')

        # Remove the file if it exist to avoid error
        if os.path.exists(move_dir):
            os.remove(move_dir)
        os.rename(pdf_file_path, move_dir)
        signals.signal_str.emit(f'{invoice_type}: {page_num} out of {main_pdf.numPages} in {main_pdf_filename}.pdf')

    try:
        shutil.rmtree(image_path)
    except OSError:
        pass
