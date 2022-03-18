import os

from PySide6.QtCore import QThread, QObject, Signal
from script import split_pdf


class MySignals(QObject):
    signal_str = Signal(str)


class WorkerThread(QThread):
    def __init__(self, parent, folder_path, store_path, invoice_type):
        QThread.__init__(self, parent)
        # Instantiate signals and connect signals to the slots
        self.signals = MySignals()
        self.signals.signal_str.connect(parent.update_progress)
        self.folder_path = folder_path
        self.store_path = store_path
        self.invoice_type = invoice_type
        self.parent = parent

    def run(self):
        files = os.listdir(self.folder_path)
        # Do something on the worker thread
        self.toggle_fields(False)
        self.parent.start_button.setText("Running - Please don't exit the application until it's finished")

        for f in files:
            if not f.endswith('.pdf'):
                continue
            file_path = os.path.join(self.folder_path, f)
            split_pdf(self.invoice_type, file_path, self.store_path, self.signals)
            # Emit signals whenever you want
            # self.signals.signal_str.emit(f)
        self.signals.signal_str.emit(f'Finished splitting all files on {self.folder_path}')
        self.toggle_fields(True)
        self.parent.start_button.setText("Start")

    def toggle_fields(self, boolean_val):
        self.parent.button_folder_path_dialog.setEnabled(boolean_val)
        self.parent.button_store_path_dialog.setEnabled(boolean_val)
        self.parent.start_button.setEnabled(boolean_val)