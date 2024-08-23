from PyQt5.QtWidgets import QMessageBox, QFileDialog
from typing import Optional


def error_dialog(message: str) -> None:
    """
    Display an error dialog with a specified message.

    Args:
        message (str): The informative text to display in the error dialog.
    """
    dialog = QMessageBox()
    dialog.setIcon(QMessageBox.Critical)
    dialog.setWindowTitle("Error")
    dialog.setText("An error occurred")
    dialog.setInformativeText(message)
    dialog.setStandardButtons(QMessageBox.Ok)
    dialog.exec_()


def select_folder_dialog() -> Optional[str]:
    """
    Display a folder selection dialog and return the selected folder path.

    Returns:
        Optional[str]: The path to the selected folder, or None if no folder was selected.
    """
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.Directory)
    dialog.setOption(QFileDialog.ShowDirsOnly, True)

    folder_path = dialog.getExistingDirectory(None, "Select Folder")

    return folder_path if folder_path else None
