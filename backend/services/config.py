import os

POSTGRES_DSN = (
    f"dbname={os.getenv('POSTGRES_DB','sim')} "
    f"user={os.getenv('POSTGRES_USER','sim')} "
    f"password={os.getenv('POSTGRES_PASSWORD','sim')} "
    f"host={os.getenv('POSTGRES_HOST','postgres')} "
    f"port={os.getenv('POSTGRES_PORT','5432')}"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
