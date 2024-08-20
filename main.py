from controllers.controller import Controller


def main():
    # TODO: appsettings folder in user home
    controller = Controller("~/Downloads/sources/PicPyles/data/test_pile_folder")
    controller.run()


if __name__ == "__main__":
    main()
