import sys
import threading
import time
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from models.scene import Scene
from models.scene_manager import SceneManager
from views.view import MainWindow, Error_Dialog, Select_Folder_Dialog


class Controller:
    def __init__(self, path=None):
        self.app = QApplication([])

        # validate inputs
        self.path = self.validate_path(path)

        # Models
        self.model_scene = Scene()
        self.model_scene_manager = SceneManager(self.path)

        # Views
        self.view = MainWindow(self.model_scene)

        # Signals
        self.view.opengl_widget.signal_folder_selected.connect(self.load_folder)

        # local state
        self.running = True
        self.clear_scene = True
        self.background_thread = threading.Thread(target=self.modify_scene_thread, daemon=True)
        self.background_thread.start()

    def validate_path(self, path):
        if path is None or not Path(path).exists():
            path = Select_Folder_Dialog()
            print(path)
            if path is None:
                Error_Dialog("No folder was selected for viewing. Closing app.")
                sys.exit(1)
        return path

    def load_folder(self, new_folder_name):
        self.model_scene_manager.save_state()
        new_abs_path = (self.model_scene_manager.path / new_folder_name).absolute()
        self.clear_scene = True
        try:
            self.path = new_abs_path
            self.model_scene_manager = SceneManager(self.path)
        except Exception as e:
            print(f"Loading folder {new_abs_path} failed with exception {e}")
            self.path = self.model_scene_manager.path
            self.model_scene_manager = SceneManager(self.path)

    def modify_scene_thread(self):
        while self.running:
            if self.model_scene_manager.redraw_scene:
                for folder_object in self.model_scene_manager.list_folders():
                    self.model_scene.add_object(folder_object)
                for image_object in self.model_scene_manager.list_images():
                    self.model_scene.add_object(image_object)
                self.model_scene_manager.redraw_scene = False
            if self.clear_scene:
                self.model_scene.remove_all_objects()
                self.clear_scene = False
            time.sleep(0.1)
            self.model_scene.update_queue.join()  # Wait for the object to be added
        self.model_scene_manager.save_state()

    def run(self):
        self.view.show()
        self.app.exec_()
        self.running = False  # Stop the background thread
