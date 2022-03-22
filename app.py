import os
import sys

from PySide6 import QtCore, QtWidgets, QtGui

from settings import BASE_DIR, INVOICE_TYPES
from threads import WorkerThread


class MainForm(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Split")

        # Create widgets
        self.invoice_type = QtWidgets.QComboBox()
        for invoice in INVOICE_TYPES:
            self.invoice_type.addItem(invoice)

        self.folder_path = QtWidgets.QLineEdit("Folder location where to read pdf files")
        self.folder_path.setEnabled(False)
        #self.folder_path.setFixedWidth(250)
        self.store_path = QtWidgets.QLineEdit("Folder location where to store split files")
        self.store_path.setEnabled(False)
        #self.store_path.setFixedWidth(250)

        self.start_button = QtWidgets.QPushButton("Start")
        self.progress = QtWidgets.QStatusBar(self)
        self.progress.showMessage("Progress:")
        self.progress_text = QtWidgets.QLabel("Not yet started")
        self.progress.addPermanentWidget(self.progress_text)
        self.progress.setGeometry(200, 80, 250, 20)

        self.folder_path_dialog = QtWidgets.QDialog()
        self.folder_path_dialog.resize(250, 250)
        self.button_folder_path_dialog = QtWidgets.QToolButton(self.folder_path_dialog)
        self.button_folder_path_dialog.setText('Select Folder:')
        self.button_folder_path_dialog.setGeometry(QtCore.QRect(210, 10, 25, 19))
        self.button_folder_path_dialog.clicked.connect(self.open_folder_path)

        self.store_path_dialog = QtWidgets.QDialog()
        self.store_path_dialog.resize(250, 250)
        self.button_store_path_dialog = QtWidgets.QToolButton(self.store_path_dialog)
        self.button_store_path_dialog.setText('Select Folder:')
        self.button_store_path_dialog.setGeometry(QtCore.QRect(210, 10, 25, 19))
        self.button_store_path_dialog.clicked.connect(self.open_store_path)

        self.msg = QtWidgets.QMessageBox()
        self.msg.setIcon(QtWidgets.QMessageBox.Warning)
        self.msg.setText('Please choose a valid file location.')
        self.msg.setWindowTitle("Invalid File Location")

        # Create layout and add widgets
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.invoice_type)
        layout.addWidget(self.folder_path)
        layout.addWidget(self.button_folder_path_dialog)
        layout.addWidget(self.store_path)
        layout.addWidget(self.button_store_path_dialog)
        layout.addWidget(self.start_button)
        layout.addWidget(self.progress)

        # Set dialog layout
        self.setLayout(layout)

        # Add button signal to start pdf split
        self.start_button.clicked.connect(self.start_pdf_split)

    def start_pdf_split(self):
        folder_path = self.folder_path.text()
        store_path = self.store_path.text()
        invoice_type = self.invoice_type.currentText()

        if os.path.isdir(folder_path) and os.path.isdir(store_path):
            instanced_thread = WorkerThread(self, folder_path, store_path, invoice_type)
            instanced_thread.start()
        else:
            self.msg.show()

    # Create the Slots that will receive signals
    @QtCore.Slot(str)
    def update_progress(self, message):
        self.progress_text.setText(message)

    def open_folder_path(self):
        self.folder_path.setText(str(QtWidgets.QFileDialog.getExistingDirectory()))

    def open_store_path(self):
        self.store_path.setText(str(QtWidgets.QFileDialog.getExistingDirectory()))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_form = MainForm()
    main_form.resize(450, 300)
    main_form.show()
    sys.exit(app.exec())
