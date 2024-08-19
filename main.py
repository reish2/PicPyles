import numpy as np

from controllers.main_controller import PicPylesController
from models.geometry import Triangle, ImageObject

def main():
    controller = PicPylesController("~/Downloads/sources/PicPyles/data/test_pile_folder")
    # controller.add_triangle(color=(1.0, 0.0, 0.0), vertices=[(-1.0, -1.0, 0.0), (1.0, -1.0, 0.0), (0.0, 1.0, 0.0)])
    # t1 = Triangle(color=(0.0, 1.0, 0.0), position=(-1, 0, 0))
    # t2 = Triangle(color=(1.0, 0.0, 0.0), position=(1, 0, 0))
    # i1 = ImageObject("assets/mascott.png", position=(1, 2, 0), size=(2.0, 2.0*9/16))
    # i2 = ImageObject("assets/mascott_16_9.png", position=(-1, 2, 0), size=(2.0, 2.0*9/16))

    # imgs = []
    # for k in range(10):
    #     pos = np.random.rand(3)
    #     pos[2] = 0
    #     img = ImageObject("assets/mascott.png", position=pos, size=(2.0, 2.0))
    #     imgs.append(img)
    #     controller.add_object(img)

    # controller.add_object(t1)
    # controller.add_object(t2)
    # controller.add_object(i1)
    # controller.add_object(i2)
    controller.run()

if __name__ == "__main__":
    main()
