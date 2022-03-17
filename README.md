## PDF SPLIT
This project is used to split the pdf files and read the scanned image
and locate the details needed to provide the proper file name.

Script Flow:
- Iterate to the files from directory
- Split the pdf file using PyPDF2 library
- Convert the splitted pdf files to jpg image using pdf2image library
- Read the image using pytesseract and opencv library
- Rename the file based on retrieve PO#, Date, and Total value from the image

Requirements:
- Windows 7 above