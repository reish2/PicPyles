from controllers.main_controller import PicPylesController

def main():
    controller = PicPylesController()
    # controller.add_triangle(color=(1.0, 0.0, 0.0), vertices=[(-1.0, -1.0, 0.0), (1.0, -1.0, 0.0), (0.0, 1.0, 0.0)])
    controller.add_triangle(color=(0.0, 1.0, 0.0), center=(-1,0,0))
    controller.add_triangle(color=(1.0, 0.0, 0.0), center=(1, 0, 0))
    controller.run()

if __name__ == "__main__":
    main()
