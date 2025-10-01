import os

# --- Servicio HTTP ---
SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8081"))

# --- Seguridad ---
API_KEY = os.getenv("API_KEY")  # UNA sola clave, sin alias

# --- SMTP ---
SMTP_SERVER = os.getenv("SMTP_SERVER")

smtp_port_env = os.getenv("SMTP_PORT")
SMTP_PORT = int(smtp_port_env) if smtp_port_env is not None else None

SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS")
SMTP_TIMEOUT_SECONDS = int(os.getenv("SMTP_TIMEOUT_SECONDS", "30"))

# --- Base de datos ---
DATABASE_DIR = os.getenv("DATABASE_DIR", "./data")
DATABASE_NAME = os.getenv("DATABASE_NAME", "messaging.db")
DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_NAME)

# --- Worker/cola ---
QUEUE_MAXSIZE = int(os.getenv("QUEUE_MAXSIZE", "100"))