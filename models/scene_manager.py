from pathlib import Path
import json
from tkinter import Image

from models.geometry import ImageObject


class SceneManager:
    # TODO: where to call SceneManager from? maybe PicPylesController.modify_scene_thread()
    def __init__(self, path):
        self.path = Path(path)
        self.ppyles_folder = self.path / '.ppyles'
        self.images = [] # list of geometry.ImageObject
        self.folders = [] # list of geometry.ImageObject with same folder image
        self.state_file = self.ppyles_folder / 'state.json'

        if not self.ppyles_folder.exists():
            self.ppyles_folder.mkdir(parents=True)
            self.scan_directory()
            self.save_state()
        else:
            # TODO
            # * load state needs to check if images have been removed
            # * update needs to check for new images and folders, then find a good place to put them

            self.load_state()
            self.update()

    def scan_directory(self):
        """Scan the directory for images and subdirectories."""
        supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')
        self.images = []
        self.folders = []

        # TODO
        # * place new items in grid somewhere close to origin
        # * create image objects for each image and folder

        for item in self.path.iterdir():
            if item.is_file() and item.suffix.lower() in supported_formats:
                self.images.append(item.name)
            elif item.is_dir() and item.name != '.ppyles':
                self.folders.append(item.name)

        self.save_state()

    def save_state(self):
        """Save the current state to the .ppyles folder."""
        images = {_.to_dict() for _ in self.images}
        folders = {_.to_dict() for _ in self.folders}
        state = {
            'images': images,
            'folders': folders
        }
        with self.state_file.open('w') as f:
            json.dump(state, f, indent=4)

    def load_state(self):
        """Load the state from the .ppyles folder."""
        # TODO
        # * save and load of serialized ImageObjects
        if self.state_file.exists():
            with self.state_file.open('r') as f:
                state = json.load(f)
                self.images = {ImageObject.from_dict(dict(_)) for _ in state.get('images', [])}
                self.folders = {ImageObject.from_dict(dict(_)) for _ in state.get('folders', [])}
        else:
            self.scan_directory()

    def add_image(self, image_name):
        """Add an image to the list and update the state."""
        if image_name not in self.images:
            self.images.append(image_name)
            self.save_state()

    def remove_image(self, image_name):
        """Remove an image from the list and update the state."""
        if image_name in self.images:
            self.images.remove(image_name)
            self.save_state()

    def update(self):
        """Re-scan the directory to update images and folders."""
        self.scan_directory()

    def list_images(self):
        """Return the list of images."""
        return self.images

    def list_folders(self):
        """Return the list of subdirectories."""
        return self.folders
