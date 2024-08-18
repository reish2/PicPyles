import numpy as np
from OpenGL.GL import *
from PIL import Image


class SceneObject:
    def __init__(self, position, size, color=None):
        self.position = np.array(position).astype(np.float64)
        self.size = np.array(size).astype(np.float64)
        self.color = color if color is not None else (1.0, 1.0, 1.0)
        self.vertices = self.create_vertices()
        self.selected = False

    def create_vertices(self):
        """
        Create the vertices based on the position and size of the object.
        This method can be overridden by subclasses to define specific shapes.
        """
        half_size = self.size / 2.0
        return np.array([
            [-half_size[0], -half_size[1], 0.0],
            [half_size[0], -half_size[1], 0.0],
            [half_size[0], half_size[1], 0.0],
            [-half_size[0], half_size[1], 0.0]
        ]) + self.position

    def update_position(self, dxyz):
        self.position += np.array(dxyz)
        self.vertices = self.create_vertices()

    def render(self):
        self.render_object()
        if self.selected:
            self.render_bounding_box()

    def render_object(self):
        """
        Render the object. This method should be overridden by subclasses to define specific drawing logic.
        """
        glBegin(GL_QUADS)
        if self.color:
            glColor3f(*self.color)
        for vertex in self.vertices:
            glVertex3f(*vertex)
        glEnd()

    def render_bounding_box(self):
        # Calculate the bounding box corners based on the object's vertices
        min_corner = [0, 0, 0]
        max_corner = [0, 0, 0]
        if isinstance(self.vertices, np.ndarray):
            min_corner = np.min(self.vertices, axis=0)
            max_corner = np.max(self.vertices, axis=0)
        else:
            verts = [v[0] for v in self.vertices]
            min_corner = np.min(verts, axis=0)
            max_corner = np.max(verts, axis=0)

        glColor3f(1.0, 1.0, 1.0)  # Red color for the bounding box
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


class Triangle(SceneObject):
    def __init__(self, color, position, size=np.array((1.0, 1.0, 0.0))):
        super().__init__(position, size, color)
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


class ImageObject(SceneObject):
    def __init__(self, image_path, position, size):
        super().__init__(position, size)
        self.image_path = image_path
        self.texture_id = None

    def load_texture(self):
        if self.texture_id is not None:
            return self.texture_id

        try:
            image = Image.open(self.image_path)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
            img_data = image.convert("RGBA").tobytes()
            width, height = image.size

            self.size = np.array([self.size[1] / height * width, self.size[1]])
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
