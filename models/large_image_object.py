from pathlib import Path

from models.image_object import ImageObject
from models.types import *


class LargeImageObject(ImageObject):
    """
    Represents a larger version of an ImageObject, typically used for detailed viewing.
    """

    def __init__(self, image_object: ImageObject) -> None:
        """
        Initialize a LargeImageObject based on an existing ImageObject.

        Args:
            image_object (ImageObject): The ImageObject instance to be enlarged.
        """
        size: Vec3 = (10.0, 10.0 * 9.0 / 16.0)  # Enlarged size, maintaining the aspect ratio.
        position: Vec3 = np.array([0.0, 0.0, 0.1])  # Position slightly above the original plane.
        parent_dir: Path = Path(image_object.image_path).parent

        super().__init__(
            image_path=image_object.image_path,
            position=position,
            size=size,
            name=image_object.text,
            parent_dir=parent_dir,
            object_type=image_object.object_type,
            use_thumbnail=False  # Don't use a thumbnail for the large image.
        )
