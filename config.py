import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/entropyai")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

# Plug-and-play auth
API_KEY_HEADER = "X-API-Key"  # keep compatibility with your existing approach :contentReference[oaicite:4]{index=4}

# Controller defaults
DEFAULT_ENERGY_BUDGET = float(os.getenv("DEFAULT_ENERGY_BUDGET", "100.0"))
LAMBDA_ENERGY = float(os.getenv("LAMBDA_ENERGY", "0.45"))

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Pub/Sub
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
PUBSUB_TOPIC = os.getenv("PUBSUB_TOPIC", "entropyai-inference-events")
PUBSUB_SUBSCRIPTION = os.getenv("PUBSUB_SUBSCRIPTION", "entropyai-inference-events-sub")

# Rate limit defaults (tune later)
RL_REQUESTS_PER_MINUTE = int(os.getenv("RL_REQUESTS_PER_MINUTE", "60"))
