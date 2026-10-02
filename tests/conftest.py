import os

os.environ["ENVIRONMENT"] = "test"
os.environ["TESTING"] = "True"
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
