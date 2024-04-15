import enum


class Entity(str, enum.Enum):
    FAMILY = "FAMILY"
    COLLECTION = "COLLECTION"
    DOCUMENT = "DOCUMENT"
    EVENT = "EVENT"
