import os

if os.environ.get("ENVIRONMENT", "local") == "local":
    from dotenv import load_dotenv

    load_dotenv()

from reliablegpt.main import reliableGPT

__all__ = ["reliableGPT"]
