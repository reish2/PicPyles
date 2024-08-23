import numpy as np
from OpenGL.GL import *

from models.scene_object import SceneObject


class Triangle(SceneObject):
    def __init__(self, position, size=np.array((1.0, 1.0, 0.0)), color=(0.0, 0.0, 1.0), text=""):
        super().__init__(position, size, color, text)
        self.vertices = self.create_vertices()

    def create_vertices(self):
        half_size = self.size / 2.0
        return np.array([
            self.position + [-half_size[0], -half_size[1], 0.0],
            self.position + [half_size[0], -half_size[1], 0.0],
            self.position + [0.0, half_size[1], 0.0]
        ])

    def render_object(self):
        glBegin(GL_TRIANGLES)
        glColor3f(*self.color)
        for vertex in self.vertices:
            glVertex3f(*vertex)
        glEnd()
