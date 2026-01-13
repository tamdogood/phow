from abc import ABC
from supabase import Client


class BaseRepository(ABC):
    """Base repository with common database operations."""

    def __init__(self, db: Client):
        self.db = db
