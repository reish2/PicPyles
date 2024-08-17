import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

class PicPylesWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PicPyles")
        self.resize(800, 600)
        self.move(100, 100)

    def show_window(self):
        self.show()

def main():
    app = QApplication(sys.argv)
    window = PicPylesWindow()
    window.show_window()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()