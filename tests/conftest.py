import os

# Settings are read at import time; the engine is created lazily-connected, so
# no database is needed for the unit tests below.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://orbitly:orbitly@localhost:5432/orbitly_test")
os.environ.setdefault("BCRYPT_ROUNDS", "4")
