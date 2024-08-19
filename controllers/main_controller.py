import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from models.scene import Scene
from models.geometry import Triangle
from models.scene_manager import SceneManager
from views.opengl_widget import PicPylesOpenGLWidget
import threading

class PicPylesWindow(QMainWindow):
    def __init__(self, scene):
        super().__init__()
        self.setWindowTitle("PicPyles")
        self.resize(800, 600)
        self.move(100, 100)
        self.opengl_widget = PicPylesOpenGLWidget(scene)
        self.setCentralWidget(self.opengl_widget)

class PicPylesController:
    def __init__(self, path=None):
        self.app = QApplication([])
        self.scene = Scene()
        if path is None:
            path = self.select_folder()
            print(path)
            if path is None:
                self.error_dialog("No folder was selected for viewing. Closing app.")
                sys.exit(1)
        self.scene_manager = SceneManager(path)
        self.window = PicPylesWindow(self.scene)
        self.running = True
        self.background_thread = threading.Thread(target=self.modify_scene_thread, daemon=True)
        self.background_thread.start()

    def select_folder(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)

        folder_path = dialog.getExistingDirectory(None, "Select Folder")

        if folder_path:
            return folder_path
        else:
            return None

    def error_dialog(self, message):
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText("An error occurred")
        error_dialog.setInformativeText(message)
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec_()

    def add_object(self, object):
        self.scene.add_object(object)

    def modify_scene_thread(self):
        # TODO:
        # * think about a file browser logic. new scene per folder with all relevant data in a .ppyle subfolder
        #   * how to interact? mouse nav buttons? hotkeys? view buttons?
        # * keep config (last viewed folder, general prefs...) in ~/.picpyle
        while self.running:
            if self.scene_manager.redraw_scene:
                for folder_object in self.scene_manager.list_folders():
                    self.scene.add_object(folder_object)
                for image_object in self.scene_manager.list_images():
                    self.scene.add_object(image_object)
                self.scene_manager.redraw_scene = False
            time.sleep(0.1)
            self.scene.update_queue.join()  # Wait for the object to be added
        self.scene_manager.save_state()

    def run(self):
        self.window.show()
        self.app.exec_()
        self.running = False  # Stop the background thread
