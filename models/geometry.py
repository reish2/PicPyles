from OpenGL.GL import *
import numpy as np
from PIL import Image

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

class ImageObject(SceneObject):
    def __init__(self, image_path, position, size):
        self.image_path = image_path
        self.position = np.array(position)
        self.size = np.array(size)
        self.texture_id = None  # Delay texture loading
        self.vertices = self.create_vertices()

    def load_texture(self):
        if self.texture_id is not None:
            return self.texture_id  # Texture already loaded

        try:
            image = Image.open(self.image_path)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)  # Flip the image vertically for OpenGL
            img_data = image.convert("RGBA").tobytes()
            width, height = image.size

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
            print(f"Texture loaded successfully with ID {texture_id}")
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

    def render(self):
        if self.texture_id is None:
            self.load_texture()  # Load the texture on first render

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

        # Check for OpenGL errors
        error = glGetError()
        if error != GL_NO_ERROR:
            print(f"OpenGL Error: {error}")