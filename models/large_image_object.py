from pathlib import Path

from models.image_object import ImageObject


class LargeImageObject(ImageObject):
    def __init__(self, image_object):
        size = (10.0, 10.0 * 9.0 / 16.0)
        position = (0, 0, 0.1)
        parent_dir = Path(image_object.image_path).parent
        super().__init__(image_object.image_path, position, size, image_object.text, parent_dir,
                         image_object.object_type, False)
