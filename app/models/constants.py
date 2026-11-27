from enum import StrEnum


class OutboxStatus(StrEnum):
    NEW = "new"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
