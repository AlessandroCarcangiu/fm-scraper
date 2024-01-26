import os


DEBUG = False
cpu_num = os.cpu_count()
NUM_PROCESSORS = int(cpu_num/3) if cpu_num > 3 else 1
MAX_THREAD_WORKERS = 5
MAX_RETRIES = 20
MAX_WAIT_SECONDS = 25
