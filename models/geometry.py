from OpenGL.GL import *
import numpy as np

class SceneObject:
    def __init__(self, color, vertices):
        self.color = color
        self.vertices = vertices

    def render(self):
        glBegin(GL_TRIANGLES)
        glColor3f(*self.color)
        for vertex in self.vertices:
            glVertex3f(*vertex)
        glEnd()

class Triangle(SceneObject):
    def __init__(self, color, center):
        self.color = color
        self.center = np.array(center)
        self.vertices = np.array(((-0.5, -0.5, 0.0), (0.5, -0.5, 0.0), (0.0, 0.5, 0.0))) + self.center
