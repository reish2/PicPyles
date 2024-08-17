import time
from PyQt5.QtWidgets import QApplication, QMainWindow
from models.scene import Scene
from models.geometry import Triangle
from views.opengl_widget import PicPylesOpenGLWidget
import threading

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
        self.running = True
        self.background_thread = threading.Thread(target=self.modify_scene_thread, daemon=True)
        self.background_thread.start()

    def add_object(self, object):
        self.scene.add_object(object)

    def modify_scene_thread(self):
        while self.running:
            # Example: Adding and removing objects periodically
            triangle = Triangle(color=(0.0, 0.0, 1.0), center=(0,-1,0))
            time.sleep(1)
            print("adding triangle")
            self.scene.add_object(triangle)
            self.scene.update_queue.join()  # Wait for the object to be added
            time.sleep(1)
            print("removing triangle")
            self.scene.remove_object(triangle)
            self.scene.update_queue.join()  # Wait for the object to be removed

    def run(self):
        self.window.show()
        self.app.exec_()
        self.running = False  # Stop the background thread
