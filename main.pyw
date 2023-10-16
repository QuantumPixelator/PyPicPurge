# PyPicPurge: A Python script to delete similar images from a folder and subfolders.
# Author: Quantum Pixelator

import os
import cv2
import shutil
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QFileDialog, QLabel

# Supported file extensions
supported_extensions = ('.bmp', '.dib', '.jpeg', '.jpg', '.jpe', '.jp2', '.png', '.webp', '.pbm', '.pgm', '.ppm', '.pxm', '.pnm', '.sr', '.ras', '.tiff', '.tif')

class Worker(QThread):
    update_log = Signal(str)
    update_count = Signal(int)
    processing_done = Signal()

    def __init__(self, folder_path, reference_image_path):
        super().__init__()
        self.folder_path = folder_path
        self.reference_image_path = reference_image_path

def run(self):
    deleted_count = 0
    deleted_folder = os.path.join(self.folder_path, "deleted_images")
    reference_image = cv2.imread(self.reference_image_path)

    if reference_image is None:
        self.update_log.emit("Error: Could not read the reference image. Moving it to 'deleted_images'.")
        if not os.path.exists(deleted_folder):
            os.makedirs(deleted_folder)
        shutil.move(self.reference_image_path, os.path.join(deleted_folder, os.path.basename(self.reference_image_path)))
        deleted_count += 1
        self.update_count.emit(deleted_count)
        self.processing_done.emit()
        return

    for root, dirs, files in os.walk(self.folder_path):
        self.update_log.emit(f"Processing subfolder: {root}")  # Inform user about the subfolder
        for file in files:
            if file.lower().endswith(supported_extensions):  # Check if the file has a supported extension
                img_path = os.path.join(root, file)
                img = cv2.imread(img_path)
                
                if img is None:
                    self.update_log.emit(f"Error: Could not read image {img_path}. Moving it to 'deleted_images'.")
                    shutil.move(img_path, os.path.join(deleted_folder, os.path.basename(img_path)))
                    deleted_count += 1
                    self.update_count.emit(deleted_count)
                    continue

                img1_gray = cv2.cvtColor(reference_image, cv2.COLOR_BGR2GRAY)
                img2_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                res = cv2.matchTemplate(img1_gray, img2_gray, 3)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                if max_val > 0.9:
                    self.update_log.emit(f"Moving similar image: {img_path}")
                    if not os.path.exists(deleted_folder):
                        os.makedirs(deleted_folder)
                    shutil.move(img_path, os.path.join(deleted_folder, os.path.basename(img_path)))
                    deleted_count += 1
                    self.update_count.emit(deleted_count)

    self.processing_done.emit()

def main():
    global log_text, image_label, deleted_count_label, select_image_button, delete_button, image_path, worker
    app = QApplication([])

    window = QWidget()
    window.setWindowTitle('Image Deleter')
    layout = QVBoxLayout()

    log_text = QTextEdit()
    log_text.setReadOnly(True)
    log_text.setPlaceholderText('Logs will appear here...')
    select_image_button = QPushButton('Select Reference Image')
    delete_button = QPushButton('Select Folder To Start')
    image_label = QLabel("Selected Image Appears Here")
    deleted_count_label = QLabel("Deleted Files: 0")

    select_image_button.clicked.connect(select_reference_image)
    delete_button.clicked.connect(start_process)

    stylesheet = """
        QWidget {
            font-size: 16px;
        }
        QTextEdit {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        QPushButton {
            background-color: #FF8700;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px;
            min-width: 200px;
        }
        QPushButton:pressed {
            background-color: #CA6B00;
        }
    """
    app.setStyleSheet(stylesheet)

    layout.addWidget(image_label)
    layout.addWidget(deleted_count_label)
    layout.addWidget(log_text)
    layout.addWidget(select_image_button)
    layout.addWidget(delete_button)

    window.setLayout(layout)
    window.show()

    app.exec()

def select_reference_image():
    global image_path  # Declare image_path as global
    image_path, _ = QFileDialog.getOpenFileName(None, "Select Image", "", "Images (*.png *.jpg *.jpeg, *.bmp, *.gif, *.tiff, *.tif, *.webp, *.avif, *.svg, *.ico, *.bpg, *.heif, *.heic)")
    if image_path:
        pixmap = QPixmap(image_path)
        image_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))

# Declare the worker as a global variable
global worker

def start_process():
    global image_path, worker  # Declare image_path and worker as global
    select_image_button.setDisabled(True)
    delete_button.setDisabled(True)
    log_text.append("Processing...")
    
    folder_path = QFileDialog.getExistingDirectory(None, "Select Folder")
    
    if folder_path and image_path:
        worker = Worker(folder_path, image_path)  # Assign Worker instance to the global worker variable
        worker.update_log.connect(update_log)
        worker.update_count.connect(update_count)
        worker.processing_done.connect(finish_process)
        worker.start()

def finish_process():
    select_image_button.setDisabled(False)
    delete_button.setDisabled(False)
    log_text.append("Job complete!")

def update_log(message):
    log_text.append(message)

def update_count(count):
    deleted_count_label.setText(f"Deleted Files: {count}")

if __name__ == '__main__':
    image_path = None  # Initialize image_path
    main()
