import sys, os, json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTextEdit,
    QPushButton, QVBoxLayout, QWidget, QLabel, QMessageBox
)
from core.uasset_reader import read_asset_file

class UassetViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FNaF Security Breach - Modding Tool")
        self.setGeometry(100, 100, 600, 450)

        self.asset_data = {}
        self.label = QLabel("No file loaded.")
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)

        self.open_file_button = QPushButton("Open .uasset/.umap")
        self.open_file_button.clicked.connect(self.load_single_file)

        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.load_folder)

        self.save_button = QPushButton("Export JSON(s)")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.export_jsons)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.open_file_button)
        layout.addWidget(self.open_folder_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.text_edit)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_single_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Unreal Assets (*.uasset *.umap)")
        if file_path:
            actors = read_asset_file(file_path)
            if actors:
                self.asset_data = {os.path.basename(file_path): actors}
                self.label.setText(f"Loaded: {file_path}")
                self.text_edit.setText("\n".join(actor["name"] for actor in actors))
                self.save_button.setEnabled(True)
            else:
                self.label.setText("Invalid or unsupported file.")
                self.text_edit.setText("")
                self.save_button.setEnabled(False)

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.asset_data = {}
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith(".uasset") or file.endswith(".umap"):
                        full_path = os.path.join(root, file)
                        actors = read_asset_file(full_path)
                        if actors:
                            self.asset_data[file] = actors

            if self.asset_data:
                self.label.setText(f"Loaded {len(self.asset_data)} files from folder.")
                sample = next(iter(self.asset_data.values()))
                self.text_edit.setText("\n".join(actor["name"] for actor in sample))
                self.save_button.setEnabled(True)
            else:
                self.label.setText("No valid .uasset/.umap files found.")
                self.text_edit.setText("")
                self.save_button.setEnabled(False)

    def export_jsons(self):
        export_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if export_dir:
            try:
                for filename, actor_data in self.asset_data.items():
                    out_path = os.path.join(export_dir, filename + ".json")
                    wrapped_data = {"actors": actor_data}
                    with open(out_path, 'w', encoding='utf-8') as f:
                        json.dump(wrapped_data, f, indent=2)
                QMessageBox.information(self, "Success", f"Exported {len(self.asset_data)} files.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = UassetViewer()
    viewer.show()
    sys.exit(app.exec_())
