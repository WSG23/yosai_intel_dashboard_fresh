class _Base:
    def __init__(self, *args, **kwargs):
        if "children" in kwargs:
            self.children = kwargs.pop("children")
        elif len(args) == 1:
            self.children = args[0]
        else:
            self.children = list(args)
        for k, v in kwargs.items():
            setattr(self, k, v)


class Card(_Base):
    pass


class Navbar(_Base):
    pass


class NavbarBrand(_Base):
    pass


class Container(_Base):
    pass


class Row(_Base):
    pass


class Col(_Base):
    pass


class Modal(_Base):
    pass


class ModalHeader(_Base):
    pass


class ModalBody(_Base):
    pass


class ModalFooter(_Base):
    pass


class ModalTitle(_Base):
    pass


class Alert(_Base):
    pass


class Button(_Base):
    pass


class Table(_Base):
    pass


class CardHeader(_Base):
    pass


class CardBody(_Base):
    pass


class Label(_Base):
    pass


class Input(_Base):
    pass


class Badge(_Base):
    pass


class Checklist(_Base):
    pass


class Nav(_Base):
    pass


class NavItem(_Base):
    pass


class NavLink(_Base):
    pass


NavbarToggler = Collapse = DropdownMenu = lambda *a, **k: None
DropdownMenuItem = lambda *a, **k: None
