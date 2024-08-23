from typing import Optional, Union, Tuple

import PyQt5
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtCore import QPoint, QEvent, Qt
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtGui import QSurfaceFormat, QWheelEvent
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QOpenGLWidget

from models.large_image_object import LargeImageObject
from models.scene_object import SceneObject


class MainWindow(QMainWindow):
    """
    Main window for the PicPyles application, containing the OpenGL widget.
    """

    def __init__(self, scene: SceneObject) -> None:
        """
        Initialize the MainWindow with a given scene.

        Args:
            scene (SceneObject): The scene to be displayed in the OpenGL widget.
        """
        super().__init__()
        self.setWindowTitle("PicPyles")
        self.resize(800, 600)
        self.move(100, 100)

        # Create and set the OpenGL widget as the central widget
        self.opengl_widget = OpenGLWidget(scene)
        self.setCentralWidget(self.opengl_widget)


class OpenGLWidget(QOpenGLWidget):
    """
    OpenGL widget for rendering the scene and handling user interactions.
    """

    signal_folder_selected = pyqtSignal(str)
    signal_enlarge_image = pyqtSignal(LargeImageObject)
    signal_close_image = pyqtSignal(LargeImageObject)

    def __init__(self, scene: SceneObject) -> None:
        """
        Initialize the OpenGLWidget with the given scene.

        Args:
            scene (SceneObject): The scene to render within the widget.
        """
        super().__init__()
        self.setFormat(self.get_opengl_format())  # Set the format with MSAA (Multi-Sample Anti-Aliasing)

        self.scene = scene
        self.done = False

        # Mouse state tracking
        self.last_mouse_pos: Optional[Tuple[int, int]] = None
        self.current_button: Optional[int] = None

        # Selection box and results
        self.selection_start: Optional[Tuple[int, int]] = None  # Start point of the selection rectangle
        self.selection_end: Optional[Tuple[int, int]] = None  # End point of the selection rectangle
        self.clicked_object: Optional[SceneObject] = None
        self.selected_objects: list[SceneObject] = []

        # Camera settings
        self.translation_x: float = 0.0
        self.translation_y: float = 0.0
        self.translation_z: float = -10.0
        self.tz_min: float = -0.1
        self.tz_max: float = -100.0
        self.focal_length: float = 1000.0  # Focal length in mm
        self.sensor_size: Tuple[int, int] = (800, 600)  # Sensor size in pixels
        self.aspect_ratio: float = self.sensor_size[0] / self.sensor_size[1]

        # Set up a timer to trigger regular redraws
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # Approximately 60 frames per second

    def get_opengl_format(self) -> QSurfaceFormat:
        """
        Get the OpenGL surface format with Multi-Sample Anti-Aliasing (MSAA).

        Returns:
            QSurfaceFormat: The surface format configured for MSAA.
        """
        format = QSurfaceFormat()
        format.setSamples(4)  # Set the number of samples for MSAA
        return format

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Handle the mouse wheel event to zoom in and out of the scene.

        Args:
            event (QWheelEvent): The mouse wheel event.
        """
        factor = max(abs(2 * (self.translation_z - self.tz_min) / (self.tz_max - self.tz_min)), 0.05)
        self.translation_z += event.angleDelta().y() * 0.02 * factor
        self.translation_z = self.tz_min if self.translation_z >= self.tz_min else self.translation_z
        self.translation_z = self.tz_max if self.translation_z <= self.tz_max else self.translation_z
        self.update()

    def reset_selected_bounding_boxes(self) -> None:
        """
        Reset the selection status of all selected objects.
        """
        print(f"reset_selected_bounding_boxes for {len(self.selected_objects)}")
        for obj in self.selected_objects:
            obj.selected = False

    def set_selected_bounding_boxes(self) -> None:
        """
        Set the selection status for all currently selected objects.
        """
        print(f"set_selected_bounding_boxes for {len(self.selected_objects)}")
        with self.scene.lock:
            for obj in self.selected_objects:
                obj.selected = True

    def reset_all_bounding_boxes(self) -> None:
        """
        Reset the selection status of all objects in the scene.
        """
        with self.scene.lock:
            print(f"reset_all_bounding_boxes for {len(self.scene.objects)}")
            for obj in self.scene.objects:
                obj.selected = False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle the mouse press event. Detects clicks on objects and initiates actions based on the click type.

        Args:
            event (QMouseEvent): The mouse event containing information about the click.
        """
        self.last_mouse_pos = event.pos()
        self.current_button = event.button()

        # Query the scene for the object at the clicked position
        self.clicked_object = self.get_clicked_object(self.last_mouse_pos)

        # Handle double-clicks and different object types
        if event.type() == QEvent.MouseButtonDblClick and self.clicked_object:
            if self.clicked_object.object_type == "folder":
                folder_name = self.clicked_object.text
                self.signal_folder_selected.emit(folder_name)
                return
            if self.clicked_object.object_type == "image" and not isinstance(self.clicked_object, LargeImageObject):
                large_image = LargeImageObject(self.clicked_object)
                large_image.move_to(np.array([-self.translation_x, -self.translation_y, 0.001]))
                self.signal_enlarge_image.emit(large_image)
                return
            if isinstance(self.clicked_object, LargeImageObject):
                self.signal_close_image.emit(self.clicked_object)
                return

        # Handle single clicks and multi-selection logic
        if self.clicked_object:
            print(f"Object clicked: {self.clicked_object}")
            if not self.selected_objects:
                # If multi-select is empty, add the clicked object
                self.selected_objects = [self.clicked_object]
                self.set_selected_bounding_boxes()
            elif self.clicked_object not in self.selected_objects:
                # If a new object is selected, reset and add the new object
                self.reset_selected_bounding_boxes()
                self.selected_objects = [self.clicked_object]
                self.set_selected_bounding_boxes()
        else:
            # No objects hit => start a new multi-select box
            self.reset_selected_bounding_boxes()
            self.selected_objects = []
            print("No object clicked.")
            if event.button() == Qt.LeftButton:
                self.selection_start = event.pos()
                self.selection_end = event.pos()

    def get_clicked_object(self, click_point: Union[QPoint, Tuple[int, int]]) -> Optional[SceneObject]:
        """
        Get the object clicked by the user in the scene.

        Args:
            click_point (Union[QPoint, Tuple[int, int]]): The position of the mouse click.

        Returns:
            Optional[SceneObject]: The object that was clicked, or None if no object was clicked.
        """
        click_pos_3d = self.get_image_plane_3d_click_coordinate(click_point)
        cam_pos = np.array([self.translation_x, self.translation_y, self.translation_z])
        clicked_object = self.scene.query(cam_pos, click_pos_3d)
        return clicked_object

    def get_image_plane_3d_click_coordinate(self, click_point: Union[QPoint, Tuple[int, int]]) -> np.ndarray:
        """
        Convert the 2D click position into a 3D coordinate on the image plane.

        Args:
            click_point (Union[QPoint, Tuple[int, int]]): The position of the mouse click.

        Returns:
            np.ndarray: The 3D coordinate on the image plane.
        """
        x, y = (click_point.x(), click_point.y()) if isinstance(click_point, QPoint) else click_point
        width = self.width()
        height = self.height()
        click_pos_3d = np.array([x - width / 2, -(y - height / 2), self.focal_length])
        return click_pos_3d

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Handle the mouse move event. Updates object positions or the selection box depending on the state.

        Args:
            event (QMouseEvent): The mouse event containing information about the movement.
        """
        if self.last_mouse_pos is not None:
            dx = event.pos().x() - self.last_mouse_pos.x()
            dy = event.pos().y() - self.last_mouse_pos.y()

            if self.current_button == Qt.LeftButton and self.selected_objects:
                # Move selected objects
                for obj in self.selected_objects:
                    if isinstance(obj, SceneObject):
                        new_position = np.array([
                            dx * -self.translation_z / self.focal_length,
                            dy * self.translation_z / self.focal_length,
                            0.0
                        ])
                        obj.update_position(new_position)
            elif self.current_button == Qt.LeftButton and self.clicked_object is None:
                # Update the multi-select box
                self.selection_end = event.pos()
            elif self.current_button in [Qt.MidButton, Qt.MiddleButton]:
                # Update the camera position when MMB is pressed
                self.translation_x += dx * -self.translation_z / self.focal_length
                self.translation_y -= dy * -self.translation_z / self.focal_length

            self.update()
        self.last_mouse_pos = event.pos()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        Handle the mouse release event. Finalizes the selection process.

        Args:
            event (QMouseEvent): The mouse event containing information about the release.
        """
        self.last_mouse_pos = None
        self.current_button = None
        self.clicked_object = None

        if self.selection_start and self.selection_end:
            # Finalize the selection of objects within the selection rectangle
            click_start_3d = self.get_image_plane_3d_click_coordinate(self.selection_start)
            click_end_3d = self.get_image_plane_3d_click_coordinate(self.selection_end)
            cam_pos = np.array([self.translation_x, self.translation_y, self.translation_z])
            self.selected_objects = self.scene.query_inside(cam_pos, click_start_3d, click_end_3d)
            self.set_selected_bounding_boxes()
            print("Selection rectangle:", self.selection_start, self.selection_end, len(self.selected_objects))

        self.selection_start = None
        self.selection_end = None

    def initializeGL(self) -> None:
        """
        Initialize OpenGL settings for the widget.
        Enables multisampling, line and point smoothing, blending, and depth testing.
        """
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_POINT_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.9, 0.9, 1.0, 1.0)
        glEnable(GL_DEPTH_TEST)

    def update_camera(self) -> None:
        """
        Update the camera settings, adjusting the perspective and translating the view
        based on the current camera position.
        """
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        fovy = 2 * np.degrees(np.arctan(self.sensor_size[1] / (2 * self.focal_length)))
        gluPerspective(fovy, self.aspect_ratio, abs(self.tz_min) * 0.9, abs(self.tz_max) * 1.1)
        glTranslatef(self.translation_x, self.translation_y, self.translation_z)

    def setup_geometry(self) -> None:
        """
        Render all the objects in the scene that have loaded thumbnails.
        """
        with self.scene.lock:
            for obj in self.scene.objects:
                if obj.has_thumbnail:
                    obj.render()

    def paintGL(self) -> None:
        """
        The main painting function, called whenever the OpenGL widget needs to be redrawn.
        Updates the camera and renders the scene's geometry.
        """
        self.update_camera()
        self.setup_geometry()
        self.draw_selection_rectangle()

    def draw_selection_rectangle(self) -> None:
        """
        Draw a selection rectangle on the screen, used for multi-selecting objects.
        """
        if self.selection_start is None or self.selection_end is None:
            return

        start = self.selection_start
        end = self.selection_end

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width(), self.height(), 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(2.0)

        glBegin(GL_LINE_LOOP)
        glVertex2i(start.x(), start.y())
        glVertex2i(end.x(), start.y())
        glVertex2i(end.x(), end.y())
        glVertex2i(start.x(), end.y())
        glEnd()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def resizeGL(self, w: int, h: int) -> None:
        """
        Handle the resizing of the OpenGL widget.

        Args:
            w (int): The new width of the widget.
            h (int): The new height of the widget.
        """
        glViewport(0, 0, w, h)
        self.aspect_ratio = w / h
        self.sensor_size = (w, h)

    def showEvent(self, event: PyQt5.QtGui.QShowEvent) -> None:
        """
        Handle the show event, ensuring the widget is updated when first shown.

        Args:
            event (QShowEvent): The show event triggering this function.
        """
        if not self.done:
            self.update()
            self.done = True
        super().showEvent(event)