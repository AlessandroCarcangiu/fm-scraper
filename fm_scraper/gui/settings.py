from queue import Queue
from multiprocessing import Manager, Queue


# custom signals
SIGNAL_SCRAPING_COMPLETED = "SIGNAL_SCRAPING_COMPLETED"
SIGNAL_TABLE_LOADED_DATA = "SIGNAL_TABLE_LOADED_DATA"
SIGNAL_TABLE_EMPTY = "SIGNAL_TABLE_EMPTY"

# labels
GUI_MAIN_TITLE = "FM-Scraper"

# main item tags
MAIN_WINDOW_TAG = "main_window"
WINDOW_PROCESS_DATA_TAG = "options_window"
WINDOW_TABLE_TAG = "table_window"
TABLE_TAG = "data_table"
MESSAGE_LOG_TEXT_TAG = "log_field"
WINDOW_SCRAPING_TAG = "window_scraping"
MODAL_MESSAGE_LOG_TAG = "modal_log"
BUTTON_MODAL_EXIT_TAG = "log_exit_button"

# queue
MESSAGE_QUEUE = None# = Queue()
def set_queue(q):
    global MESSAGE_QUEUE
    MESSAGE_QUEUE = q


# window sizes
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 900
WINDOW_MAX_WIDTH = 600
WINDOW_MAX_HEIGHT = 600
