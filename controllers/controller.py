import json
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication

from models.image_object import ImageObject
from models.large_image_object import LargeImageObject
from models.scene import Scene
from models.scene_manager import SceneManager
from views.view import MainWindow

from views.utils import *

class Controller:
    """
    Controller class that orchestrates the application's flow, manages state,
    and coordinates interactions between the models and views.
    """

    def __init__(self, assets_path: Path, path: Path = None):
        """
        Initialize the Controller, load the application state, and set up the main components.

        Args:
            path (Path, optional): The path to the directory or file to load. Defaults to None.
        """
        self.app = QApplication([])

        self.assets_path = assets_path

        # Load previous state if available
        self.load_app_state()

        # Validate input path
        if path and self.path:
            self.path = self.validate_path(path)
        else:
            self.path = self.validate_path(self.path)

        # Models
        self.model_scene = Scene()
        self.model_scene_manager = SceneManager(self.path, self.assets_path)

        # Views
        self.view = MainWindow(self.model_scene,self.assets_path)
        self.model_scene.start_update_timer()  # Fix image load failure on first few images
        self.view.set_current_path(self.path)

        # Signals
        self.reconnect_view_signals()
        self.reconnect_msm_signals()

        # Local state
        self.running = True
        self.clear_scene = True

        self.rescan_folder_and_update_scene()

    def __del__(self):
        """Ensure the state is saved when the Controller is deleted (on application close)."""
        self.save_app_state()

    def load_app_state(self) -> None:
        """
        Load application state from ~/.picpyles/appsettings.json if it exists.
        """
        settings_path = Path.home() / ".picpyles/appsettings.json"
        if settings_path.exists():
            try:
                with open(settings_path, 'r') as f:
                    state = json.load(f)
                    self.path = Path(state.get('last_opened_path')).resolve().absolute()
                    # Load any additional state variables here
            except Exception as e:
                print(f"Failed to load app state: {e}")

    def save_app_state(self) -> None:
        """
        Save application state to ~/.picpyles/appsettings.json.
        """
        settings_dir = Path.home() / ".picpyles"
        settings_path = settings_dir / "appsettings.json"

        # Create the settings directory if it doesn't exist
        if not settings_dir.exists():
            settings_dir.mkdir(parents=True)

        # Prepare the state data to save
        state = {
            "last_opened_path": str(Path(self.path).resolve().absolute()),
            # Add any additional state variables you want to save here
        }

        # Save the state as a JSON file
        try:
            with open(settings_path, 'w') as f:
                json.dump(state, f)
            print(f"App state saved to {settings_path}")
        except Exception as e:
            print(f"Failed to save app state: {e}")

    def rescan_folder_and_update_scene(self) -> None:
        """
        Rescan the current folder and update the scene with the latest objects.
        """
        self.model_scene_manager.scan_directory()
        self.model_scene_manager.load_objects_into_scene()
        self.model_scene.sync_objects(self.model_scene_manager.list_all_objects())

    def reconnect_view_signals(self) -> None:
        """
        Reconnect the signals from the view to the appropriate slots in the controller.
        """
        self.view.opengl_widget.signal_folder_selected.connect(self.load_folder)
        self.view.opengl_widget.signal_enlarge_image.connect(self.enlarge_image)
        self.view.opengl_widget.signal_close_image.connect(self.close_enlarge_image)

    def reconnect_msm_signals(self) -> None:
        """
        Reconnect the signals from the SceneManager to the appropriate slots in the controller.
        """
        self.model_scene_manager.signal_add_image.connect(self.add_image_to_scene)

    def validate_path(self, path: Path) -> Path:
        """
        Validate the provided path. If it's invalid or None, prompt the user to select a folder.

        Args:
            path (Path): The path to validate.

        Returns:
            Path: The validated path.

        Raises:
            SystemExit: If no valid path is provided or selected.
        """
        if path is None or not path.exists():
            path = select_folder_dialog()
            print(path)
            if path is None:
                error_dialog("No folder was selected for viewing. Closing app.")
                sys.exit(1)
        return path

    def add_image_to_scene(self, image_object: ImageObject) -> None:
        """
        Add an image object to the scene.

        Args:
            image_object: The image object to add.
        """
        self.model_scene.add_object(image_object)

    def enlarge_image(self, large_image_object: LargeImageObject) -> None:
        """
        Add a large image object to the scene for enlargement.

        Args:
            large_image_object: The large image object to add.
        """
        self.model_scene.add_object(large_image_object)

    def close_enlarge_image(self, large_image_object: LargeImageObject) -> None:
        """
        Remove the large image object from the scene.

        Args:
            large_image_object: The large image object to remove.
        """
        self.model_scene.remove_object(large_image_object)

    def load_folder(self, new_folder_name: str) -> None:
        """
        Load a new folder, save the current state, and update the scene with the contents
        of the new folder.

        Args:
            new_folder_name (str): The name of the new folder to load.
        """
        self.model_scene_manager.save_state()
        new_abs_path = (self.model_scene_manager.path / new_folder_name).resolve().absolute()
        self.model_scene.remove_all_objects()
        try:
            self.path = new_abs_path
            self.model_scene_manager = SceneManager(self.path, self.assets_path)
        except Exception as e:
            print(f"Loading folder {new_abs_path} failed with exception {e}")
            self.path = self.model_scene_manager.path
            self.model_scene_manager = SceneManager(self.path, self.assets_path)
        self.reconnect_msm_signals()
        self.model_scene_manager.load_objects_into_scene()
        self.view.set_current_path(self.path)

    def run(self) -> None:
        """
        Run the main application loop, displaying the main window and starting the Qt event loop.
        """
        self.view.show()
        self.app.exec_()
        self.running = False  # Stop the background thread
