class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __eq__(self, other: object) -> bool:
        if (isinstance(other, User)):
            if (other.id != self.id):
                return False
            elif (other.name != self.name):
                return False
            else:
                return True
        return False
