from controllers.main_controller import PicPylesController
from models.geometry import Triangle, ImageObject

def main():
    controller = PicPylesController()
    # controller.add_triangle(color=(1.0, 0.0, 0.0), vertices=[(-1.0, -1.0, 0.0), (1.0, -1.0, 0.0), (0.0, 1.0, 0.0)])
    t1 = Triangle(color=(0.0, 1.0, 0.0), center=(-1,0,0))
    t2 = Triangle(color=(1.0, 0.0, 0.0), center=(1, 0, 0))
    i1 = ImageObject("assets/mascott.png", position=(0, 2, 0), size=(2.0, 2.0))
    controller.add_object(t1)
    controller.add_object(t2)
    controller.add_object(i1)
    controller.run()

if __name__ == "__main__":
    main()
