import sys
import ollama
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton,
                             QVBoxLayout, QWidget, QFileDialog, QComboBox,
                             QTextEdit, QHBoxLayout, QScrollArea, QSpacerItem,QSizePolicy)
from PyQt6.QtGui import QPixmap, QImage, QGuiApplication
from PyQt6.QtCore import Qt, QTimer
from enum import Enum

class CopyState(Enum):
  READY = 0
  SUCCESS = 1
  ERROR = 2

class ImageAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.copy_state = CopyState.READY
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Llama3.2 Vision Textprompt from Picture")
        self.setGeometry(100, 100, 800, 600)

        # Hauptlayout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Bildauswahl und Anzeige in einer ScrollArea (zentriert)
        self.image_scroll_area = QScrollArea()
        self.image_label = QLabel("Kein Bild ausgewählt")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(0, 0)  # Optional: Mindestgröße
        self.image_scroll_area.setWidget(self.image_label)
        self.image_scroll_area.setWidgetResizable(True)
        self.image_scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter) # Zentriert die ScrollArea
        layout.addWidget(self.image_scroll_area)

        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.select_image_button = QPushButton("Bild auswählen")
        self.select_image_button.clicked.connect(self.select_image)
        layout.addWidget(self.select_image_button)

        # Anweisungsauswahl
        self.instruction_label = QLabel("Anweisung:")
        layout.addWidget(self.instruction_label)

        self.instruction_combo = QComboBox()
        self.load_instructions()
        layout.addWidget(self.instruction_combo)

        # Direkte Anweisungseingabe
        self.custom_instruction_label = QLabel("Oder eigene Anweisung:")
        layout.addWidget(self.custom_instruction_label)

        self.custom_instruction_input = QTextEdit()
        self.custom_instruction_input.setFixedHeight(50)
        layout.addWidget(self.custom_instruction_input)

        # Analyse Button und Textausgabe
        analyze_layout = QHBoxLayout()
        self.analyze_button = QPushButton("Textausgabe")
        self.analyze_button.clicked.connect(self.analyze_image)
        analyze_layout.addWidget(self.analyze_button)

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        layout.addWidget(self.text_output)
        layout.addLayout(analyze_layout)
        layout.addWidget(self.text_output)

        # Button zum Kopieren des Textes
        self.copy_button = QPushButton("Text in Zwischenablage kopieren")
        self.copy_button.clicked.connect(self.copy_text_to_clipboard)
        layout.addWidget(self.copy_button)

        self.image_path = None

    def load_instructions(self):
        try:
            with open("anweisungen.txt", "r") as f:
                instructions = f.read().split("\n\n")
                self.instruction_combo.addItems(instructions)
        except FileNotFoundError:
            self.instruction_combo.addItems(["Datei 'anweisungen.txt' nicht gefunden"])

    def select_image(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Bilder (*.png *.jpg *.jpeg *.bmp)")
        if file_dialog.exec():
            self.image_path = file_dialog.selectedFiles()[0]
            pixmap = QPixmap(self.image_path)

            if pixmap.width() > self.image_scroll_area.width() or pixmap.height() > self.image_scroll_area.height():
              scaled_pixmap = pixmap.scaled(self.image_scroll_area.width(), self.image_scroll_area.height(),
                                            Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
            else:
              scaled_pixmap = pixmap
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.adjustSize()

    def analyze_image(self):
      if self.image_path:
        selected_instruction = self.instruction_combo.currentText()
        custom_instruction = self.custom_instruction_input.toPlainText().strip()

        instruction = custom_instruction if custom_instruction else selected_instruction

        if not instruction or instruction == "Datei 'anweisungen.txt' nicht gefunden":
            self.text_output.setText("Bitte eine Anweisung auswählen oder eingeben.")
            return
        try:
          self.text_output.setText("Analysiere...")
          QApplication.processEvents()
          response = ollama.chat(
            model='llama3.2-vision',
            messages=[
            {
              'role': 'user',
              'content': instruction,
              'images': [self.image_path]
            }
          ])

          self.text_output.setText(response['message']['content'])
        except Exception as e:
          self.text_output.setText(f"Fehler bei der Analyse: {e}")
      else:
          self.text_output.setText("Bitte zuerst ein Bild auswählen.")

    def copy_text_to_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        text = self.text_output.toPlainText()
        if text:
            clipboard.setText(text)
            self.copy_state = CopyState.SUCCESS
        else:
            self.copy_state = CopyState.ERROR
        self.update_copy_button_style()
        QTimer.singleShot(2000, self.reset_copy_button_style)

    def update_copy_button_style(self):
        if self.copy_state == CopyState.SUCCESS:
            self.copy_button.setStyleSheet("background-color: green; color: white;")
        elif self.copy_state == CopyState.ERROR:
            self.copy_button.setStyleSheet("background-color: red; color: white;")
        else:
            self.copy_button.setStyleSheet("")

    def reset_copy_button_style(self):
        self.copy_state = CopyState.READY
        self.update_copy_button_style()

def main():
    app = QApplication(sys.argv)
    main_window = ImageAnalyzerApp()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
