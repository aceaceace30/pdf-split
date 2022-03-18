import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POPPLER_PATH = os.path.join(BASE_DIR, 'dependencies', 'poppler/poppler-22.01.0/Library/bin')
PATH_TO_TESSERACT = os.path.join(BASE_DIR, 'dependencies', 'Tesseract-OCR/tesseract.exe')

FACTORY_MOTOR_PARTS = "FMP"
NAPA_MOTOR_PARTS = "NAPA"
INVOICE_TYPES = (NAPA_MOTOR_PARTS, FACTORY_MOTOR_PARTS)
