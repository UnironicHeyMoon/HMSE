from numpy import isin


class Asset:
    def __init__(self, id : int, name: str) -> None:
        self._id = id
        self._name = name.upper()
    
    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    def __eq__(self, other: object) -> bool:
        if (isinstance(other, Asset)):    
            return other.id == self.id and other.name == self.name
        else:
            return False
    def __hash__(self) -> int:
        return self.id
