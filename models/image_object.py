import concurrent.futures
import threading
from pathlib import Path

import numpy as np
from OpenGL.GL import *
from PIL import Image

from models.scene_object import SceneObject


class ImageObject(SceneObject):
    # Initialize the thread pool
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def __init__(self, image_path, position, size, name=None, parent_dir=None, object_type="image", use_thumbnail=True):
        self.use_thumbnail = use_thumbnail
        self.image_path = image_path
        self.object_type = object_type  # "image" or "folder"
        if parent_dir:
            self.image_path = Path(parent_dir) / image_path
        if not name:
            name = Path(image_path).name
        super().__init__(position, size, text=name)
        self.texture_id = None

        self.has_thumbnail = False

        self.lock = threading.Lock()
        self.executor.submit(self.update_thumbnail)

    def move_to(self, position):
        if isinstance(position, np.ndarray):
            if len(position) == 3:
                self.position = position

    def update_thumbnail(self):
        with self.lock:
            img_path = Path(self.image_path)
            self.thumbnail_folder = img_path.absolute().parent / ".ppyles" / "thumbnails"
            self.thumbnail_path = self.thumbnail_folder / img_path.name
            if not self.thumbnail_folder.exists():
                self.thumbnail_folder.mkdir(parents=True)
            if not self.thumbnail_path.exists():
                self.create_thumbnail()
            self.has_thumbnail = True

    def create_thumbnail(self):
        # Check if the image path exists
        img_path = Path(self.image_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Image file {self.image_path} not found.")

        # Open the image using PIL
        with Image.open(self.image_path) as img:
            # Convert the image to RGB (if not already in that mode)
            img = img.convert("RGB")

            # Create the thumbnail
            img.thumbnail((512, 512))

            # Save the thumbnail to the specified path
            img.save(self.thumbnail_path, "JPEG")
            print(f"Thumbnail saved to {self.thumbnail_path}")

    def to_dict(self, preserve_image_path=False):
        # dict keys must be kept consistant with __init__(**kwargs)
        if preserve_image_path:
            return {"image_path": self.image_path, "position": list(self.position), "size": list(self.size),
                    "name": self.text, "object_type": self.object_type}
        else:
            return {"image_path": Path(self.image_path).name, "position": list(self.position), "size": list(self.size),
                    "name": self.text, "object_type": self.object_type}

    def load_texture(self):
        if self.has_thumbnail is None:
            return

        if self.texture_id is not None:
            return self.texture_id

        try:
            if self.use_thumbnail:
                image = Image.open(self.thumbnail_path)
            else:
                image = Image.open(self.image_path)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
            img_data = image.convert("RGBA").tobytes()
            width, height = image.size
            sx, sy = self.size
            scale_factor = min(sx, sy) / (min(width, height))

            self.size = np.array([width * scale_factor, height * scale_factor])
            self.vertices = self.create_vertices()

            texture_id = glGenTextures(1)
            if texture_id == 0:
                raise ValueError("Failed to generate texture")

            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
            glGenerateMipmap(GL_TEXTURE_2D)

            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            glBindTexture(GL_TEXTURE_2D, 0)

            self.texture_id = texture_id
            return texture_id
        except Exception as e:
            print(f"Failed to load texture: {e}")
            return 0

    def create_vertices(self):
        half_size = self.size / 2.0
        bottom_left = self.position + np.array([-half_size[0], -half_size[1], 0.0])
        bottom_right = self.position + np.array([half_size[0], -half_size[1], 0.0])
        top_left = self.position + np.array([-half_size[0], half_size[1], 0.0])
        top_right = self.position + np.array([half_size[0], half_size[1], 0.0])

        vertices = [
            (bottom_left, (0.0, 0.0)),
            (bottom_right, (1.0, 0.0)),
            (top_right, (1.0, 1.0)),
            (top_right, (1.0, 1.0)),
            (top_left, (0.0, 1.0)),
            (bottom_left, (0.0, 0.0)),
        ]
        return vertices

    def render_object(self):
        if self.has_thumbnail is None:
            return

        if self.texture_id is None:
            self.load_texture()

        if self.texture_id == 0:
            print("No valid texture to render.")
            return

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        # Ensure we are using white color to avoid color modulation
        glColor3f(1.0, 1.0, 1.0)

        glBegin(GL_TRIANGLES)
        for vertex, tex_coord in self.vertices:
            glTexCoord2f(*tex_coord)
            glVertex3f(*vertex)
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

        # Render the bounding box if the object is selected
        if self.selected:
            self.render_bounding_box()

        # Check for OpenGL errors
        error = glGetError()
        if error != GL_NO_ERROR:
            print(f"OpenGL Error: {error}")
