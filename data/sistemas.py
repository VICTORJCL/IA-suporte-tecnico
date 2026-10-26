import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ACELERATO_URL = os.getenv("ACELERATO_URL", "")
ACELERATO_EMAIL_SOLICITANTE = os.getenv("ACELERATO_EMAIL_SOLICITANTE", "")
ZANTHUS_URL = os.getenv("ZANTHUS_URL", "")
BLUESOFT_URL = os.getenv("BLUESOFT_URL", "")
PAINEL_URL = os.getenv("PAINEL_URL", "")
