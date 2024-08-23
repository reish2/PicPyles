import numpy as np
from OpenGL.GL import *
from typing import Tuple, Optional

from models.scene_object import SceneObject

Vec3 = np.ndarray


class Triangle(SceneObject):
    """
    Represents a triangular object in the scene, derived from SceneObject.
    """

    def __init__(self, position: Vec3, size: Vec3 = np.array((1.0, 1.0, 0.0)),
                 color: Tuple[float, float, float] = (0.0, 0.0, 1.0), text: str = ""):
        """
        Initialize the Triangle with a position, size, color, and optional text.

        Args:
            position (Vec3): The (x, y, z) position of the triangle.
            size (Vec3): The (width, height, depth) size of the triangle. Defaults to (1.0, 1.0, 0.0).
            color (Tuple[float, float, float]): The color of the triangle in RGB format. Defaults to blue.
            text (str): Optional text to display on the triangle. Defaults to an empty string.
        """
        super().__init__(position, size, color, text)
        self.vertices = self.create_vertices()

    def create_vertices(self) -> Vec3:
        """
        Create the vertices for the triangle based on its position and size.

        Returns:
            Vec3: An array of vertices representing the triangle's corners.
        """
        half_size = self.size / 2.0
        return np.array([
            self.position + [-half_size[0], -half_size[1], 0.0],
            self.position + [half_size[0], -half_size[1], 0.0],
            self.position + [0.0, half_size[1], 0.0]
        ])

    def render_object(self) -> None:
        """
        Render the triangle using OpenGL.
        """
        glBegin(GL_TRIANGLES)
        glColor3f(*self.color)
        for vertex in self.vertices:
            glVertex3f(*vertex)
        glEnd()
