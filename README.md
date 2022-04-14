# PDF SPLIT
This project is used to split the pdf files and locate the details needed to provide the proper file name.

### Script Flow:
- Iterate to the files from directory
- Split the pdf file using PyPDF2 library
- Convert the splitted pdf files to jpg image using pdf2image library
- Enhance and read the image using pytesseract and opencv library
- Rename the file based on retrieved PO#, Date, and Total value from the image

### Requirements:
- Windows 7 above
- Python 3.8 or above (Optional if you want to package the application)

### Running the application:
- Download the poppler and tesseract-ocr on the official website
- Create a folder on the root of project named `dependencies`
- Extract the poppler and tesseract-ocr folders to the `dependencies` folder
- Run -> pip install -r requirements.txt
- Run -> python app.py

### Package the application:
- pip install PyInstaller
- pyinstaller -n "pdf-split" app.py

### Supported invoice and file format:
- FMP (Factory Motor Parts) - (PO # - DATE - TOTAL)
- NAPA (NAPA Motor Parts) - (PO # - DATE - TOTAL)
