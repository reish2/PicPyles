import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject
from numpy import arange

from models.image_object import ImageObject


class SceneManager(QObject):
    """
    Manages the state of the scene, including loading and saving image and folder objects,
    scanning directories, and emitting signals to update the scene.
    """

    signal_add_image = pyqtSignal(ImageObject)

    def __init__(self, path: Path):
        """
        Initialize the SceneManager, load the scene state, and scan the directory.

        Args:
            path (Path): The path to the directory containing the scene.
        """
        super().__init__()
        self.path = Path(path)
        self.ppyles_folder = self.path / '.ppyles'
        self.state_file = self.ppyles_folder / 'state.json'

        self.min_pos = np.array((0.0, 0.0, 0.0))
        self.max_pos = np.array((0.0, 0.0, 0.0))
        self.default_image_size = (2.0, 2.0 * 9.0 / 16.0)
        self.default_image_spacing = tuple(1.125 * _ for _ in self.default_image_size)

        self.images: List[ImageObject] = []
        self.folders: List[ImageObject] = [
            ImageObject("assets/parent_folder.jpg", np.array((0.0, 0.0, 0.0)), self.default_image_size, "..",
                        object_type="folder")
        ]

        if not self.ppyles_folder.exists():
            self.ppyles_folder.mkdir(parents=True)
            self.scan_directory()
        else:
            self.load_state()
            self.scan_directory()  # scan for changes

    def __del__(self):
        """Ensure the state is saved when the SceneManager is deleted."""
        self.save_state()

    def scan_directory(self) -> None:
        """
        Scan the directory for images and subdirectories. Updates the scene
        with new images and folders, and removes any missing ones.
        """
        supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')

        # 1. Find all folder contents (non-recursive)
        # 2. Split sets into new and old images. Old images already have a position and size; new ones don't.
        old_image_names = [img.image_path.name for img in self.images]
        old_folder_names = [folder.text for folder in self.folders]

        all_image_names_in_folder = []
        all_folder_names_in_folder = [".."]
        new_image_names = []
        new_folder_names = []

        for item in self.path.iterdir():
            if item.is_file() and item.suffix.lower() in supported_formats:
                new_image = item.name
                all_image_names_in_folder.append(new_image)
                if new_image not in old_image_names:
                    new_image_names.append(new_image)
            elif item.is_dir() and item.name != '.ppyles':
                new_folder = item.name
                all_folder_names_in_folder.append(new_folder)
                if new_folder not in old_folder_names:
                    new_folder_names.append(new_folder)

        # Remove anything that is no longer present to avoid crashes on load
        self.images = [img for img in self.images if img.image_path.name in all_image_names_in_folder]
        self.folders = [folder for folder in self.folders if folder.text in all_folder_names_in_folder]

        # Sort new items
        new_image_names.sort(key=str.lower)
        new_folder_names.sort(key=str.lower)

        # 3. Construct a grid for new folders and images outside and to the right of the current pile
        new_grid_offset = np.array((self.max_pos[0] + self.default_image_spacing[0], self.min_pos[1], 0.0))
        new_object_count = len(new_image_names) + len(new_folder_names)
        if new_object_count > 0:
            self.redraw_scene = True
            grid_dim = int(np.ceil(np.sqrt(new_object_count)))
            u_, v_ = np.meshgrid(arange(grid_dim), arange(grid_dim))
            u_ = u_.flatten()
            v_ = v_.flatten()

            for k, new_folder_name in enumerate(new_folder_names):
                w, h = self.default_image_spacing
                new_pos = np.array((u_[k] * w, -v_[k] * h, 0.0)) + new_grid_offset
                new_folder_object = ImageObject(
                    "assets/folder2.jpg", new_pos, self.default_image_size, new_folder_name, object_type="folder"
                )
                self.folders.append(new_folder_object)

            for k, new_image_name in enumerate(new_image_names):
                w, h = self.default_image_spacing
                new_pos = np.array((u_[k + len(new_folder_names)] * w, -v_[k + len(new_folder_names)] * h, 0.0)) + new_grid_offset
                new_image_object = ImageObject(
                    new_image_name, new_pos, self.default_image_size, new_image_name, parent_dir=self.path, object_type="image"
                )
                self.images.append(new_image_object)

        self.save_state()

    def load_objects_into_scene(self) -> None:
        """Load all folders and images into the scene by emitting signals."""
        for folder in self.folders:
            self.signal_add_image.emit(folder)
        for img in self.images:
            self.signal_add_image.emit(img)

    def save_state(self) -> None:
        """Save the current state to the .ppyles folder."""
        images = [img.to_dict() for img in self.images]
        folders = [folder.to_dict(preserve_image_path=True) for folder in self.folders]
        state = {
            'images': images,
            'folders': folders
        }
        with self.state_file.open('w') as f:
            json.dump(state, f, indent=4)

    def load_state(self) -> None:
        """Load the state from the .ppyles folder."""
        self.redraw_scene = True
        if self.state_file.exists():
            try:
                with self.state_file.open('r') as f:
                    state = json.load(f)
                    self.images = [ImageObject(**img, parent_dir=self.path) for img in state.get('images', [])]
                    self.folders = [ImageObject(**folder) for folder in state.get('folders', [])]
            except json.JSONDecodeError as e:
                print(f"Failed to load state file {self.state_file}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        else:
            self.scan_directory()

        positions = [img.position for img in self.images] + [folder.position for folder in self.folders]
        if positions:
            positions = np.vstack(positions)
            self.min_pos = np.min(positions, axis=0)
            self.max_pos = np.max(positions, axis=0)

    def list_images(self) -> List[ImageObject]:
        """Return the list of images."""
        return self.images

    def list_folders(self) -> List[ImageObject]:
        """Return the list of subdirectories."""
        return self.folders

    def list_all_objects(self) -> List[ImageObject]:
        """Return the combined list of images and subdirectories."""
        return self.images + self.folders
