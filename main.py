import sys
import ollama
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton,
                             QVBoxLayout, QWidget, QFileDialog, QComboBox,
                             QTextEdit, QHBoxLayout, QSizePolicy, QDialog,
                             QDialogButtonBox, QFormLayout)
from PyQt6.QtGui import QPixmap, QGuiApplication, QTextOption, QFont
from PyQt6.QtCore import Qt, QTimer, QMimeData
from enum import Enum
import os

class CopyState(Enum):
    READY = 0
    SUCCESS = 1
    ERROR = 2

class AnalyzeState(Enum):
    READY = 0
    SUCCESS = 1
    ERROR = 2

class TextEditDialog(QDialog):
    def __init__(self, initial_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Text bearbeiten")
        self.setModal(True)
        self.edited_text = None

        # Schriftart und -größe festlegen
        font = QFont()
        font.setPointSize(16)
        self.setFont(font)

        # Layout erstellen
        layout = QVBoxLayout()

        # Textedit-Feld
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(initial_text)
        layout.addWidget(self.text_edit)

        # Dialog-Schaltflächen (OK und Abbrechen)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_text(self):
        return self.text_edit.toPlainText()

class ImageAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.copy_state = CopyState.READY
        self.analyze_state = AnalyzeState.READY
        self.initUI()
        self.setAcceptDrops(True)

        # Schriftart und -größe festlegen
        font = QFont()
        font.setPointSize(16)
        self.setFont(font)

    def initUI(self):
        self.setWindowTitle("Prompt from picture with llama3.2-vision | from www.der-zerfleischer.de")
        self.setFixedSize(600, 620)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Bildauswahl und Anzeige (ohne ScrollArea)
        self.image_label = QLabel("Kein Bild ausgewählt")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedHeight(200)
        layout.addWidget(self.image_label)

        self.select_image_button = QPushButton("Bild auswählen")
        self.select_image_button.clicked.connect(self.select_image)
        layout.addWidget(self.select_image_button)

        self.instruction_label = QLabel("Anweisung:")
        layout.addWidget(self.instruction_label)

        self.instruction_combo = QComboBox()
        self.instruction_combo.setMinimumHeight(50)
        self.instruction_combo.setMaximumWidth(600)
        self.load_instructions()
        layout.addWidget(self.instruction_combo)

        self.custom_instruction_label = QLabel("Oder eigene Anweisung:")
        layout.addWidget(self.custom_instruction_label)

        self.custom_instruction_input = QTextEdit()
        self.custom_instruction_input.setFixedHeight(50)
        layout.addWidget(self.custom_instruction_input)

        analyze_layout = QHBoxLayout()
        self.analyze_button = QPushButton("Bild analysieren")
        self.analyze_button.clicked.connect(self.analyze_image)
        analyze_layout.addWidget(self.analyze_button)

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setFixedHeight(100)
        text_options = self.text_output.document().defaultTextOption()
        text_options.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.text_output.document().setDefaultTextOption(text_options)
        layout.addWidget(self.text_output)
        layout.addLayout(analyze_layout)

        self.copy_button = QPushButton("Text in Zwischenablage kopieren")
        self.copy_button.clicked.connect(self.copy_text_to_clipboard)
        layout.addWidget(self.copy_button)

        self.image_path = None

    def load_instructions(self):
        try:
            with open("anweisungen.txt", "r", encoding='utf-8') as f:
                instructions = [instr.strip() for instr in f.read().split("\n\n") if instr.strip()]
                if instructions:
                    self.instruction_combo.addItems(instructions)
                else:
                    self.instruction_combo.addItems(["Keine Anweisungen gefunden in 'anweisungen.txt'"])
        except FileNotFoundError:
            self.instruction_combo.addItems(["Datei 'anweisungen.txt' nicht gefunden"])

    def select_image(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Bilder (*.png *.jpg *.jpeg *.bmp *.webp)")
        if file_dialog.exec():
            self.image_path = file_dialog.selectedFiles()[0]
            self.load_image()

    def load_image(self):
        pixmap = QPixmap(self.image_path)
        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def analyze_image(self):
        if self.image_path:
            selected_instruction = self.instruction_combo.currentText()
            custom_instruction = self.custom_instruction_input.toPlainText().strip()
            instruction = custom_instruction if custom_instruction else selected_instruction

            if not instruction or instruction in ["Datei 'anweisungen.txt' nicht gefunden", "Keine Anweisungen gefunden in 'anweisungen.txt'"]:
                self.text_output.setText("Bitte eine Anweisung auswählen oder eingeben.")
                self.analyze_state = AnalyzeState.ERROR
                self.update_analyze_button_style()
                QTimer.singleShot(2000, self.reset_analyze_button_style)
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
                    ]
                )
                generated_text = response['message']['content']

                dialog = TextEditDialog(generated_text, self)
                result = dialog.exec()

                if result == QDialog.DialogCode.Accepted:
                    edited_text = dialog.get_text()
                    self.text_output.setText(edited_text)
                    self.save_text_to_file(edited_text)
                    self.analyze_state = AnalyzeState.SUCCESS
                else:
                    self.text_output.setText("Analyse abgebrochen oder kein Text übernommen.")
                    self.analyze_state = AnalyzeState.ERROR

            except ollama.OllamaError as e:
                self.text_output.setText(f"Ollama Fehler: {e}")
                self.analyze_state = AnalyzeState.ERROR
            except Exception as e:
                self.text_output.setText(f"Unerwarteter Fehler: {e}")
                self.analyze_state = AnalyzeState.ERROR

        else:
            self.text_output.setText("Bitte zuerst ein Bild auswählen.")
            self.analyze_state = AnalyzeState.ERROR

        self.update_analyze_button_style()
        QTimer.singleShot(2000, self.reset_analyze_button_style)

    def save_text_to_file(self, text):
        file_path = "llama-vision.txt"
        try:
            with open(file_path, 'a', encoding='utf-8') as file:
                file.write(text + "\n")
        except Exception as e:
            self.text_output.setText(f"Fehler beim Speichern der Datei: {e}")

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

    def update_analyze_button_style(self):
        if self.analyze_state == AnalyzeState.SUCCESS:
            self.analyze_button.setStyleSheet("background-color: green; color: white;")
        elif self.analyze_state == AnalyzeState.ERROR:
            self.analyze_button.setStyleSheet("background-color: red; color: white;")
        else:
            self.analyze_button.setStyleSheet("")

    def reset_analyze_button_style(self):
        self.analyze_state = AnalyzeState.READY
        self.update_analyze_button_style()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
                    self.image_path = file_path
                    self.load_image()
            event.accept()
        else:
            event.ignore()

def main():
    app = QApplication(sys.argv)
    main_window = ImageAnalyzerApp()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
