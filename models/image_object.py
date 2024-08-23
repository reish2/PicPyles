import concurrent.futures
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import numpy as np
from OpenGL.GL import *
from PIL import Image

from models.scene_object import SceneObject
from models.types import *

class ImageObject(SceneObject):
    """
    Represents an image object in the scene. It can load textures, create thumbnails, and render itself.
    """

    # Initialize the thread pool for concurrent thumbnail creation
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def __init__(self, image_path: str, position: Vec3, size: Vec3, name: Optional[str] = None,
                 parent_dir: Optional[str] = None, object_type: str = "image", use_thumbnail: bool = True):
        """
        Initialize the ImageObject with its image path, position, size, and other properties.

        Args:
            image_path (str): Path to the image file.
            position (Vec3): The (x, y, z) position of the image.
            size (Vec3): The (width, height, depth) size of the image.
            name (Optional[str]): Name of the image. Defaults to the image file name.
            parent_dir (Optional[str]): Directory containing the image. Defaults to None.
            object_type (str): Type of the object, either "image" or "folder". Defaults to "image".
            use_thumbnail (bool): Whether to use a thumbnail for rendering. Defaults to True.
        """
        self.use_thumbnail = use_thumbnail
        self.image_path = Path(parent_dir) / image_path if parent_dir else Path(image_path)
        self.object_type = object_type
        name = name or self.image_path.name
        super().__init__(position, size, text=name)

        self.texture_id: Optional[int] = None
        self.has_thumbnail: Optional[bool] = False

        self.lock = threading.Lock()
        self.executor.submit(self.update_thumbnail)

    def move_to(self, position: Vec3) -> None:
        """
        Move the image object to a new position.

        Args:
            position (Vec3): The new (x, y, z) position.
        """
        if isinstance(position, np.ndarray) and len(position) == 3:
            self.position = position

    def update_thumbnail(self) -> None:
        """
        Create or update the thumbnail for the image.
        """
        with self.lock:
            img_path = Path(self.image_path)
            self.thumbnail_folder = img_path.absolute().parent / ".ppyles" / "thumbnails"
            self.thumbnail_path = self.thumbnail_folder / img_path.name
            if not self.thumbnail_folder.exists():
                self.thumbnail_folder.mkdir(parents=True)
            if not self.thumbnail_path.exists():
                self.create_thumbnail()
            self.has_thumbnail = True

    def create_thumbnail(self) -> None:
        """
        Create a thumbnail for the image and save it to the .ppyles folder.
        """
        img_path = Path(self.image_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Image file {self.image_path} not found.")

        with Image.open(self.image_path) as img:
            img = img.convert("RGB")
            img.thumbnail((512, 512))
            img.save(self.thumbnail_path, "JPEG")
            print(f"Thumbnail saved to {self.thumbnail_path}")

    def to_dict(self, preserve_image_path: bool = False) -> Dict[str, Any]:
        """
        Convert the ImageObject to a dictionary representation.

        Args:
            preserve_image_path (bool): Whether to preserve the absolute image path. Defaults to False.

        Returns:
            Dict[str, Any]: The dictionary representation of the ImageObject.
        """
        if preserve_image_path:
            return {
                "image_path": str(self.image_path),
                "position": self.position.tolist(),
                "size": self.size.tolist(),
                "name": self.text,
                "object_type": self.object_type
            }
        else:
            return {
                "image_path": self.image_path.name,
                "position": self.position.tolist(),
                "size": self.size.tolist(),
                "name": self.text,
                "object_type": self.object_type
            }

    def load_texture(self) -> Optional[int]:
        """
        Load the texture from the image or its thumbnail.

        Returns:
            Optional[int]: The texture ID if successful, otherwise None.
        """
        if not self.has_thumbnail:
            return None

        if self.texture_id is not None:
            return self.texture_id

        try:
            image = Image.open(self.thumbnail_path if self.use_thumbnail else self.image_path)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
            img_data = image.convert("RGBA").tobytes()
            width, height = image.size
            sx, sy = self.size
            scale_factor = min(sx, sy) / min(width, height)

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
            return None

    def create_vertices(self) -> List[VertexWithTexCoord]:
        """
        Create the vertices for the image object based on its position and size.

        Each vertex is paired with texture coordinates, which are used for mapping textures onto the object.

        Returns:
            List[VertexWithTexCoord]: A list of tuples, where each tuple contains a vertex (as a numpy array) and
            its corresponding texture coordinates (as a tuple of two floats).
        """
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

    def render_object(self) -> None:
        """
        Render the image object using OpenGL.
        """
        if not self.has_thumbnail:
            return

        if self.texture_id is None:
            self.load_texture()

        if self.texture_id == 0:
            print("No valid texture to render.")
            return

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        glColor3f(1.0, 1.0, 1.0)

        glBegin(GL_TRIANGLES)
        for vertex, tex_coord in self.vertices:
            glTexCoord2f(*tex_coord)
            glVertex3f(*vertex)
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

        if self.selected:
            self.render_bounding_box()

        error = glGetError()
        if error != GL_NO_ERROR:
            print(f"OpenGL Error: {error}")
