import logging
import os

if not os.path.exists("logs"):
    os.mkdir("logs")

catbot_logger = logging.getLogger("meowbot")
catbot_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

catbot_logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(
    filename=f"logs/meowbot.log", mode="a", encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(catbot_formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(catbot_formatter)

catbot_logger.addHandler(file_handler)
catbot_logger.addHandler(console_handler)
