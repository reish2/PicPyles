import numpy as np
from OpenGL.GL import *
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple


class SceneObject:
    """
    Represents a 3D object in the scene, capable of rendering itself,
    displaying text, and managing its position and size.
    """

    def __init__(self, position: Tuple[float, float, float], size: Tuple[float, float, float],
                 color: Optional[Tuple[float, float, float]] = None, text: str = "Test"):
        """
        Initialize the SceneObject with a position, size, color, and optional text.

        Args:
            position (Tuple[float, float, float]): The (x, y, z) position of the object.
            size (Tuple[float, float, float]): The (width, height, depth) size of the object.
            color (Optional[Tuple[float, float, float]]): The color of the object in RGB format. Defaults to white.
            text (str): The text to be displayed on the object. Defaults to "Test".
        """
        self.position = np.array(position).astype(np.float64)
        self.size = np.array(size).astype(np.float64)
        self.color = color if color is not None else (1.0, 1.0, 1.0)
        self.vertices = self.create_vertices()
        self.selected = False
        self.text = text
        self.font_texture: Optional[Tuple[int, int, int]] = None  # Stores (texture_id, text_width, text_height)

    def create_text_texture(self, text: str, font_size: int = 80) -> Optional[Tuple[int, int, int]]:
        """
        Create an OpenGL texture from the provided text string.

        Args:
            text (str): The text to render.
            font_size (int): The size of the font. Defaults to 80.

        Returns:
            Optional[Tuple[int, int, int]]: A tuple containing the texture ID, text width, and text height.
        """
        if self.font_texture is not None:
            return self.font_texture

        try:
            font = ImageFont.truetype("assets/liberation-sans/LiberationSans-Bold.ttf", font_size)
            # Use getbbox() to calculate the size of the text
            text_bbox = font.getbbox(text)
            text_width = text_bbox[2] + 4
            text_height = text_bbox[3] + 4

            # Create an image with the text
            image = Image.new("RGBA", (text_width, text_height), color=(255, 255, 255, 0))
            draw = ImageDraw.Draw(image)
            draw.text((0, 0), text, font=font, fill=(64, 64, 80, 255))

            # Convert the image to bytes and create a texture
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
            img_data = image.convert("RGBA").tobytes()

            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_width, text_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glGenerateMipmap(GL_TEXTURE_2D)

            self.font_texture = (texture_id, text_width, text_height)
            return self.font_texture

        except Exception as e:
            print(f"Failed to load texture: {e}")
            return None

    def create_vertices(self) -> np.ndarray:
        """
        Create the vertices based on the position and size of the object.

        Returns:
            np.ndarray: An array of vertices representing the corners of the object.
        """
        half_size = self.size / 2.0
        return np.array([
            [-half_size[0], -half_size[1], 0.0],
            [half_size[0], -half_size[1], 0.0],
            [half_size[0], half_size[1], 0.0],
            [-half_size[0], half_size[1], 0.0]
        ]) + self.position

    def update_position(self, dxyz: np.ndarray) -> None:
        """
        Update the position of the object by a given displacement.

        Args:
            dxyz (np.ndarray): The displacement to apply to the object's position.
        """
        self.position += dxyz
        self.vertices = self.create_vertices()

    def render(self) -> None:
        """
        Render the object, including its bounding box if selected and text if specified.
        """
        self.render_object()
        if self.selected:
            self.render_bounding_box()
        if self.text:
            self.render_text()

    def render_text(self) -> None:
        """
        Render the text associated with the object.
        """
        if self.font_texture is None:
            self.font_texture = self.create_text_texture(self.text)

        if self.font_texture[0] == 0:
            print("No valid texture to render.")
            return

        texture_id, _text_width, _text_height = self.font_texture
        text_width, text_height = _text_width / 8, _text_height / 8

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # Enable blending
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColor3f(1.0, 1.0, 1.0)

        glPushMatrix()
        glTranslatef(self.position[0], self.position[1] - self.size[1] * (1 / 2 + 0.05), self.position[2])
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-text_width / 200.0, -text_height / 200.0, 0.0)

        glTexCoord2f(1.0, 0.0)
        glVertex3f(text_width / 200.0, -text_height / 200.0, 0.0)

        glTexCoord2f(1.0, 1.0)
        glVertex3f(text_width / 200.0, text_height / 200.0, 0.0)

        glTexCoord2f(0.0, 1.0)
        glVertex3f(-text_width / 200.0, text_height / 200.0, 0.0)
        glEnd()
        glPopMatrix()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)  # Disable blending after rendering

    def render_object(self) -> None:
        """
        Render the object. This method should be overridden by subclasses to define specific drawing logic.
        """
        glBegin(GL_QUADS)
        if self.color:
            glColor3f(*self.color)
        for vertex in self.vertices:
            glVertex3f(*vertex)
        glEnd()

    def render_bounding_box(self) -> None:
        """
        Render the bounding box around the object if it is selected.
        """
        # Calculate the bounding box corners based on the object's vertices
        min_corner = np.min(self.vertices, axis=0) if isinstance(self.vertices, np.ndarray) else [0, 0, 0]
        max_corner = np.max(self.vertices, axis=0) if isinstance(self.vertices, np.ndarray) else [0, 0, 0]

        glColor3f(1.0, 1.0, 1.0)  # White color for the bounding box
        glLineWidth(4.0)  # Thicker lines for visibility

        glBegin(GL_LINE_LOOP)
        # Front face
        glVertex3f(min_corner[0], min_corner[1], min_corner[2])
        glVertex3f(max_corner[0], min_corner[1], min_corner[2])
        glVertex3f(max_corner[0], max_corner[1], min_corner[2])
        glVertex3f(min_corner[0], max_corner[1], min_corner[2])
        glEnd()

        glBegin(GL_LINE_LOOP)
        # Back face
        glVertex3f(min_corner[0], min_corner[1], max_corner[2])
        glVertex3f(max_corner[0], min_corner[1], max_corner[2])
        glVertex3f(max_corner[0], max_corner[1], max_corner[2])
        glVertex3f(min_corner[0], max_corner[1], max_corner[2])
        glEnd()

        glBegin(GL_LINES)
        # Connect the front and back faces
        for i in range(4):
            glVertex3f(min_corner[0] if i % 2 == 0 else max_corner[0],
                       min_corner[1] if i < 2 else max_corner[1],
                       min_corner[2])
            glVertex3f(min_corner[0] if i % 2 == 0 else max_corner[0],
                       min_corner[1] if i < 2 else max_corner[1],
                       max_corner[2])
        glEnd()
