import json
from pathlib import Path

import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject
from numpy.ma.core import arange

from models.scene_objects import ImageObject


class SceneManager(QObject):
    signal_add_image = pyqtSignal(ImageObject)

    def __init__(self, path):
        super().__init__()
        self.path = Path(path)
        self.ppyles_folder = self.path / '.ppyles'
        self.state_file = self.ppyles_folder / 'state.json'

        self.min_pos = np.array((0.0, 0.0, 0.0))
        self.max_pos = np.array((0.0, 0.0, 0.0))
        self.default_image_size = (2.0, 2.0 * 9.0 / 16.0)
        self.default_image_spacing = tuple(1.125 * _ for _ in self.default_image_size)

        self.images = []  # list of geometry.ImageObject
        self.folders = [
            ImageObject("assets/parent_folder.jpg", np.array((0.0, 0.0, 0.0)), self.default_image_size, "..",
                        object_type="folder")]

        if not self.ppyles_folder.exists():
            self.ppyles_folder.mkdir(parents=True)
            self.scan_directory()
        else:
            self.load_state()
            self.scan_directory()  # scan for changes

    def __del__(self):
        self.save_state()

    def scan_directory(self):
        """Scan the directory for images and subdirectories."""
        supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')

        # 1. find all folder contents (dont recurse)
        # 2. split sets into new and old images. old images already have a posituiona and size. new ones dont.
        old_image_names = [_.image_path.name for _ in self.images]
        old_folder_names = [_.text for _ in self.folders]

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
                    new_folder_names.append(item.name)

        # remove anything that is no longer present. we dont want to crash on load
        for img in self.images:
            if img.image_path.name not in all_image_names_in_folder:
                self.images.remove(img)
        for folder in self.folders:
            if folder.text not in all_folder_names_in_folder:
                self.folders.remove(folder)

        # sort new items
        new_image_names.sort(key=str.lower)
        new_folder_names.sort(key=str.lower)

        # 3. construct a grid for new folders and images that is outside and to the right of the current pile
        new_grid_offset = np.array((self.max_pos[0] + self.default_image_spacing[0], self.min_pos[1], 0.0))
        new_image_count = len(new_image_names)
        new_folder_count = len(new_folder_names)
        new_object_count = new_image_count + new_folder_count
        if new_object_count > 0:
            self.redraw_scene = True
            grid_dim = np.ceil(np.sqrt(len(new_image_names) + len(new_folder_names)))
            u_, v_ = np.meshgrid(arange(grid_dim), arange(grid_dim))
            u_ = u_.flatten()
            v_ = v_.flatten()
            for k, new_folder_name in enumerate(new_folder_names):
                w, h = self.default_image_spacing
                new_pos = np.array((u_[k] * w, -v_[k] * h, 0.0)) + new_grid_offset
                new_folder_object = ImageObject("assets/folder2.jpg", new_pos, self.default_image_size, new_folder_name,
                                                object_type="folder")
                self.folders.append(new_folder_object)
            for k, new_image_name in enumerate(new_image_names):
                w, h = self.default_image_spacing
                new_pos = np.array((u_[k + new_folder_count] * w, -v_[k + new_folder_count] * h, 0.0)) + new_grid_offset
                new_image_object = ImageObject(new_image_name, new_pos, self.default_image_size, new_image_name,
                                               parent_dir=self.path, object_type="image")
                self.images.append(new_image_object)

        self.save_state()

    def load_objects_into_scene(self):
        for fld in self.folders:
            self.signal_add_image.emit(fld)
        for img in self.images:
            self.signal_add_image.emit(img)

    def save_state(self):
        """Save the current state to the .ppyles folder."""
        images = [_.to_dict() for _ in self.images]
        folders = [_.to_dict(preserve_image_path=True) for _ in self.folders]
        state = {
            'images': images,
            'folders': folders
        }
        with self.state_file.open('w') as f:
            json.dump(state, f, indent=4)

    def load_state(self):
        """Load the state from the .ppyles folder."""
        self.redraw_scene = True
        if self.state_file.exists():
            try:
                with self.state_file.open('r') as f:
                    state = json.load(f)
                    self.images = [ImageObject(**_, parent_dir=self.path) for _ in state.get('images', [])]
                    self.folders = [ImageObject(**_) for _ in state.get('folders', [])]
            except json.JSONDecodeError as e:
                print(f"Failed to load state file {self.state_file}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        else:
            self.scan_directory()

        positions = []
        if len(self.images) > 0:
            positions = [_.position for _ in self.images]
        if len(self.folders) > 0:
            positions += [_.position for _ in self.folders]

        if len(positions) > 0:
            positions = np.vstack(positions)
            self.min_pos = np.min(positions, axis=0)
            self.max_pos = np.max(positions, axis=0)

    def list_images(self):
        """Return the list of images."""
        return self.images

    def list_folders(self):
        """Return the list of subdirectories."""
        return self.folders

    def list_all_objects(self):
        return self.images + self.folders
