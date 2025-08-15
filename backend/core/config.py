import os

from dotenv import load_dotenv


def load_config() -> None:
    load_dotenv(override=True)


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_API_KEY is None:
    raise Exception("Missing openai api key")


MODEL = "gpt-4o-mini"
