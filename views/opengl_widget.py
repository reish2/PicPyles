from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

class PicPylesOpenGLWidget(QOpenGLWidget):
    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.done = False
        self.last_mouse_pos = None
        self.translation_x = 0.0
        self.translation_y = 0.0
        self.translation_z = -10.0
        self.tz_min = -5
        self.tz_max = -500
        self.focal_length = 50.0  # Focal length in mm
        self.sensor_size = (36.0, 24.0)  # Sensor size in mm
        self.aspect_ratio = self.sensor_size[0] / self.sensor_size[1]

        # Set up a timer to trigger regular redraws
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # Approximately 60 frames per second

    def wheelEvent(self, event):
        self.translation_z += event.angleDelta().y() * 0.02
        self.translation_z = self.tz_min if self.translation_z >= self.tz_min else self.translation_z
        self.translation_z = self.tz_max if self.translation_z <= self.tz_max else self.translation_z
        self.update()

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()
        self.current_button = event.button()

        # Get the current viewport and matrices
        width = self.width()
        height = self.height()

        # Query the scene for the object at the clicked position
        cam_pos = np.array((self.translation_x, self.translation_y, self.translation_z))
        click_pos_3d = np.array((event.x()-width/2, -(event.y()-height/2), self.focal_length))
        self.clicked_object = self.scene.query(cam_pos, click_pos_3d)

        if self.clicked_object:
            print(f"Object clicked: {self.clicked_object}")
        else:
            print("No object clicked.")


    def mouseMoveEvent(self, event):
        if self.last_mouse_pos is not None:
            dx = event.pos().x() - self.last_mouse_pos.x()
            dy = event.pos().y() - self.last_mouse_pos.y()

            if self.current_button == Qt.LeftButton and isinstance(self.clicked_object, SceneObject):
                # Update the image position when LMB is pressed
                self.clicked_object.update_position((dx * -self.translation_z / self.focal_length,
                                     dy * self.translation_z / self.focal_length,
                                     0))

            elif self.current_button == Qt.MidButton or self.current_button == Qt.MiddleButton:
                # Update the camera position when MMB is pressed
                self.translation_x += dx * -self.translation_z / self.focal_length
                self.translation_y -= dy * -self.translation_z / self.focal_length

            self.update()

        self.last_mouse_pos = event.pos()

    def mouseReleaseEvent(self, event):
        self.last_mouse_pos = None
        self.current_button = None
        self.clicked_object = None

    def initializeGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.9, 0.9, 1.0, 1.0)
        glEnable(GL_DEPTH_TEST)

    def update_camera(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        fovy = 2 * np.atan(self.sensor_size[1] / (2 * self.focal_length)) * 180 / np.pi
        gluPerspective(fovy, self.aspect_ratio, 1, abs(self.tz_max) + 10)  # Set up a 3D projection matrix
        glTranslatef(self.translation_x, self.translation_y, self.translation_z)

    def setup_geometry(self):
        with self.scene.lock:
            for obj in self.scene.objects:
                obj.render()

    def paintGL(self):
        self.update_camera()
        if self.scene.process_updates():  # Handle pending updates to the scene
            self.update()  # Trigger a repaint if there were updates
        self.setup_geometry()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.aspect_ratio = w / h

    def showEvent(self, event):
        if not self.done:
            self.update()
            self.done = True
        super().showEvent(event)
