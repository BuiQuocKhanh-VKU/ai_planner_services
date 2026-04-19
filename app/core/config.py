import os

MODEL_PATH = os.getenv("MODEL_PATH", "./model")
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "256"))