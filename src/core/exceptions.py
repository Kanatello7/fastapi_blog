class RepositoryError(Exception):
    pass


class UniqueConstraintError(RepositoryError):
    pass


class ForeignKeyConstraintError(RepositoryError):
    def __init__(self, constraint_name: str):
        self.constraint_name = constraint_name
