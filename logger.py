import datetime


class Logger:
    COLOR_RESET = "\033[0m"
    COLOR_RED = "\033[91m"
    COLOR_GREEN = "\033[92m"
    COLOR_YELLOW = "\033[93m"
    COLOR_BLUE = "\033[94m"
    COLOR_MAGENTA = "\033[95m"
    COLOR_CYAN = "\033[96m"

    @staticmethod
    def log(message, log_type="INFO"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color_code = Logger.COLOR_RESET
        if log_type == "INFO":
            color_code = Logger.COLOR_GREEN
        elif log_type == "WARNING":
            color_code = Logger.COLOR_YELLOW
        elif log_type == "ERROR":
            color_code = Logger.COLOR_RED

        print(f"[{timestamp}] [{color_code}{log_type}{Logger.COLOR_RESET}] {message}")
