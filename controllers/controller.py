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
        self.model_scene.start_update_timer() # fix image load failure on first few images

        # Signals
        self.reconnect_view_signals()
        self.reconnect_msm_signals()

        # local state
        self.running = True
        self.clear_scene = True

        self.rescan_folder_and_update_scene()

    def rescan_folder_and_update_scene(self):
        self.model_scene_manager.scan_directory()
        self.model_scene_manager.load_objects_into_scene()
        self.model_scene.sync_objects(self.model_scene_manager.list_all_objects())

    def reconnect_view_signals(self):
        self.view.opengl_widget.signal_folder_selected.connect(self.load_folder)
        self.view.opengl_widget.signal_enlarge_image.connect(self.enlarge_image)
        self.view.opengl_widget.signal_close_image.connect(self.close_enlarge_image)

    def reconnect_msm_signals(self):
        self.model_scene_manager.signal_add_image.connect(self.add_image_to_scene)

    def validate_path(self, path):
        if path is None or not Path(path).exists():
            path = Select_Folder_Dialog()
            print(path)
            if path is None:
                Error_Dialog("No folder was selected for viewing. Closing app.")
                sys.exit(1)
        return path

    def add_image_to_scene(self, image_object):
        self.model_scene.add_object(image_object)

    def enlarge_image(self, large_image_object):
        self.model_scene.add_object(large_image_object)

    def close_enlarge_image(self, large_image_object):
        self.model_scene.remove_object(large_image_object)

    def load_folder(self, new_folder_name):
        self.model_scene_manager.save_state()
        new_abs_path = (self.model_scene_manager.path / new_folder_name).absolute()
        self.model_scene.remove_all_objects()
        try:
            self.path = new_abs_path
            self.model_scene_manager = SceneManager(self.path)
        except Exception as e:
            print(f"Loading folder {new_abs_path} failed with exception {e}")
            self.path = self.model_scene_manager.path
            self.model_scene_manager = SceneManager(self.path)
        self.reconnect_msm_signals()
        self.model_scene_manager.load_objects_into_scene()


    def run(self):
        self.view.show()
        self.app.exec_()
        self.running = False  # Stop the background thread
