class Select:
    def __init__(self, list_items: list) -> None:
        self.list_items = list_items

    @classmethod
    def from_args(cls, *args):
        return cls(list(args))

    def __str__(self):
        return f'$select={','.join(self.list_items)}'