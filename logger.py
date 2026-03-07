import logging
import os

if not os.path.exists("logs"):
    os.mkdir("logs")

wafbot_logger = logging.getLogger("wafbot")
wafbot_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

wafbot_logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(
    filename=f"logs/wafbot.log", mode="a", encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(wafbot_formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(wafbot_formatter)

wafbot_logger.addHandler(file_handler)
wafbot_logger.addHandler(console_handler)
