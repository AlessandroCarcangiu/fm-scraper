from multiprocessing import freeze_support
from fm_scraper.gui.pages import GUIMain


def main():
    GUIMain()


if __name__ == "__main__":
    freeze_support()
    main()
