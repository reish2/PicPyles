import PyQt5
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtCore import QTimer, Qt, QEvent, pyqtSignal
from PyQt5.QtWidgets import QOpenGLWidget, QMainWindow, QMessageBox, QFileDialog

from models.scene_objects import SceneObject


def Error_Dialog(message):
    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Critical)
    error_dialog.setWindowTitle("Error")
    error_dialog.setText("An error occurred")
    error_dialog.setInformativeText(message)
    error_dialog.setStandardButtons(QMessageBox.Ok)
    error_dialog.exec_()


def Select_Folder_Dialog():
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.Directory)
    dialog.setOption(QFileDialog.ShowDirsOnly, True)

    folder_path = dialog.getExistingDirectory(None, "Select Folder")

    if folder_path:
        return folder_path
    else:
        return None


class MainWindow(QMainWindow):
    def __init__(self, scene):
        super().__init__()
        self.setWindowTitle("PicPyles")
        self.resize(800, 600)
        self.move(100, 100)
        self.opengl_widget = OpenGLWidget(scene)
        self.setCentralWidget(self.opengl_widget)


class OpenGLWidget(QOpenGLWidget):
    signal_folder_selected = pyqtSignal(str)  # Define a signal

    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.done = False

        # mouse state tracking
        self.last_mouse_pos = None
        self.current_button = None

        # selection box and results
        self.selection_start = None  # Start point of the selection rectangle
        self.selection_end = None  # End point of the selection rectangle
        self.clicked_object = None
        self.selected_objects = []

        # camera settings
        self.translation_x = 0.0
        self.translation_y = 0.0
        self.translation_z = -10.0
        self.tz_min = -0.1
        self.tz_max = -100
        self.focal_length = 1000.0  # Focal length in mm
        self.sensor_size = (800, 600)  # Sensor size in mm
        self.aspect_ratio = self.sensor_size[0] / self.sensor_size[1]

        # Set up a timer to trigger regular redraws
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # Approximately 60 frames per second

    def wheelEvent(self, event):
        factor = np.max((abs(2 * (self.translation_z - self.tz_min) / (self.tz_max - self.tz_min)), 0.05))
        self.translation_z += event.angleDelta().y() * 0.02 * factor
        self.translation_z = self.tz_min if self.translation_z >= self.tz_min else self.translation_z
        self.translation_z = self.tz_max if self.translation_z <= self.tz_max else self.translation_z
        self.update()

    def reset_selected_bounding_boxes(self):
        print(f"reset_selected_bounding_boxes for {len(self.selected_objects)}")
        for obj in self.selected_objects:
            obj.selected = False

    def set_selected_bounding_boxes(self):
        print(f"set_selected_bounding_boxes for {len(self.selected_objects)}")
        for obj in self.selected_objects:
            obj.selected = True

    def reset_all_bounding_boxes(self):
        print(f"reset_all_bounding_boxes for {len(self.scene.objects)}")
        for obj in self.scene.objects:
            obj.selected = False

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()
        self.current_button = event.button()

        # Query the scene for the object at the clicked position
        self.clicked_object = self.get_clicked_object(self.last_mouse_pos)

        # i have several cases to handle here
        # 1. on down press, detect if an object was hit and save it
        # 2. if button stays pressed, several options
        #    * object hit on downpress
        #      * if multi-select is empty, add object to multi select list => multi move on drag
        #      * if clicked object is not in multi-select list => empty list and add clicked object => multi move
        #      * if clicked object is in multi-select list => multi move
        #    * no object hit on downpress
        #      * empty multi-select list => start new multiselect box
        # 3. on double click and clicked_object is folder => deconstruct scene and initialize new one with new path
        # Detect double-click
        if event.type() == QEvent.MouseButtonDblClick and self.clicked_object:
            if self.clicked_object:
                # Double-click detected and an object was hit
                if self.clicked_object.object_type == "folder":  # Assuming you have a FolderObject type
                    folder_name = self.clicked_object.text
                    self.signal_folder_selected.emit(folder_name)  # Emit signal
                    return

        if self.clicked_object:
            print(f"Object clicked: {self.clicked_object}")
            if not self.selected_objects:
                # multiselect is empty
                self.selected_objects = [self.clicked_object]
                self.set_selected_bounding_boxes()
            elif self.clicked_object not in self.selected_objects:
                # new object selected
                self.reset_selected_bounding_boxes()
                self.selected_objects = [self.clicked_object]
                self.set_selected_bounding_boxes()
            # else: clicked object is within the multi-select set? nothing to do! everything is already setup
        else:
            # No objects hit => empty selected objects list and start new multi select
            self.reset_selected_bounding_boxes()
            self.selected_objects = []
            print("No object clicked.")
            if event.button() == Qt.LeftButton:
                self.selection_start = event.pos()
                self.selection_end = event.pos()

    def get_clicked_object(self, click_point):
        # Get the current viewport and matrices
        click_pos_3d = self.get_image_plane_3d_click_coordinate(click_point)
        cam_pos = np.array((self.translation_x, self.translation_y, self.translation_z))
        clicked_object = self.scene.query(cam_pos, click_pos_3d)
        return clicked_object

    def get_image_plane_3d_click_coordinate(self, click_point):
        # get the 3D click coordinate on the image plane at focal_length from the camera
        if isinstance(click_point, PyQt5.QtCore.QPoint):
            x = click_point.x()
            y = click_point.y()
        else:
            # tuple
            x, y = click_point
        width = self.width()
        height = self.height()
        click_pos_3d = np.array((x - width / 2, -(y - height / 2), self.focal_length))
        return click_pos_3d

    def mouseMoveEvent(self, event):
        if self.last_mouse_pos is not None:
            dx = event.pos().x() - self.last_mouse_pos.x()
            dy = event.pos().y() - self.last_mouse_pos.y()

            if self.current_button == Qt.LeftButton and self.selected_objects:
                # we are moving selected_objects
                for obj in self.selected_objects:
                    if isinstance(obj, SceneObject):
                        new_position = (dx * -self.translation_z / self.focal_length,
                                        dy * self.translation_z / self.focal_length,
                                        0.0)
                        obj.update_position(new_position)
            elif self.current_button == Qt.LeftButton and self.clicked_object is None:
                # we are currently drawing a multi-select box
                self.selection_end = event.pos()
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

        if self.selection_start and self.selection_end:
            # Perform selection logic here, selecting objects inside the rectangle
            click_start_3d = self.get_image_plane_3d_click_coordinate(self.selection_start)
            click_end_3d = self.get_image_plane_3d_click_coordinate(self.selection_end)
            cam_pos = np.array((self.translation_x, self.translation_y, self.translation_z))
            self.selected_objects = self.scene.query_inside(cam_pos, click_start_3d, click_end_3d)
            self.set_selected_bounding_boxes()
            print("Selection rectangle:", self.selection_start, self.selection_end, len(self.selected_objects))

        self.selection_start = None
        self.selection_end = None

    def initializeGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.9, 0.9, 1.0, 1.0)
        glEnable(GL_DEPTH_TEST)

    def update_camera(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        fovy = 2 * np.atan(self.sensor_size[1] / (2 * self.focal_length)) * 180 / np.pi
        gluPerspective(fovy, self.aspect_ratio, abs(self.tz_min) * 0.9,
                       abs(self.tz_max) * 1.1)  # Set up a 3D projection matrix
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

        # Draw the selection rectangle if applicable
        self.draw_selection_rectangle()

    def draw_selection_rectangle(self):
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

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.aspect_ratio = w / h
        self.sensor_size = (w, h)

    def showEvent(self, event):
        if not self.done:
            self.update()
            self.done = True
        super().showEvent(event)
