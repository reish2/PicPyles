from PyQt5.QtWidgets import QApplication, QMainWindow
from models.scene import Scene
from models.triangle import Triangle2
from views.opengl_widget import PicPylesOpenGLWidget

class PicPylesWindow(QMainWindow):
    def __init__(self, scene):
        super().__init__()
        self.setWindowTitle("PicPyles")
        self.resize(800, 600)
        self.move(100, 100)
        self.opengl_widget = PicPylesOpenGLWidget(scene)
        self.setCentralWidget(self.opengl_widget)

class PicPylesController:
    def __init__(self):
        self.app = QApplication([])
        self.scene = Scene()
        self.window = PicPylesWindow(self.scene)

    def add_triangle(self, color, center):
        triangle = Triangle2(color=color, center=center)
        self.scene.add_object(triangle)

    def run(self):
        self.window.show()
        self.app.exec_()
