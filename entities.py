"""Drawing entity objects:
Some future ones:
GR Geometry Rectangle
GP Geometry Polygon
GO Geometry Oval
GE Geometry Ellipse
GS Geometry Slot

DA Dimension Angular
DR Dimension Radial
"""


class CL:
    """Construction Line object initialized with a tuple of attributes.

    attribs = (coords, color)
    coords = (a, b, c)
    """

    def __init__(self, attribs):
        self.coords, self.color = attribs
        self.type = 'cl'
        self.show = True

    def __hash__(self):
        return hash(self.get_attribs())
    
    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.coords == other.coords and
                self.color == other.color)

    def __repr__(self):
        return "{} object with coordinates {}".format(self.type, self.coords)

    def get_attribs(self):
        return (self.coords, self.color)

class CC:
    """Construction Circle object initialized with a tuple of attributes.

    attribs = (coords, color)
    coords = (pc, r)
    """

    def __init__(self, attribs):
        self.coords, self.color = attribs
        self.type = 'cc'
        self.show = True

    def __hash__(self):
        return hash(self.get_attribs())
    
    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.coords == other.coords and
                self.color == other.color)

    def __repr__(self):
        return "{} object with coordinates {}".format(self.type, self.coords)

    def get_attribs(self):
        return (self.coords, self.color)

class GL:
    """Geometry Line object initialized with a tuple of attributes.

    attribs = (coords, color)
    coords = (a, b, c)
    """

    def __init__(self, attribs):
        self.coords, self.color = attribs
        self.type = 'gl'
        self.show = True

    def __hash__(self):
        return hash(self.get_attribs())
    
    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.coords == other.coords and
                self.color == other.color)

    def __repr__(self):
        return "{} object with coordinates {}".format(self.type, self.coords)

    def get_attribs(self):
        return (self.coords, self.color)

class GC:
    """Geometry Circle object initialized with a tuple of attributes.

    attribs = (coords, color)
    coords = (pc, r)
    """

    def __init__(self, attribs):
        self.coords, self.color = attribs
        self.type = 'gc'
        self.show = True

    def __hash__(self):
        return hash(self.get_attribs())
    
    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.coords == other.coords and
                self.color == other.color)

    def __repr__(self):
        return "{} object with coordinates {}".format(self.type, self.coords)

    def get_attribs(self):
        return (self.coords, self.color)

class GA:
    """Geometry Arc object initialized with a tuple of attributes.

    attribs = (coords, color)
    coords = (pc, r, a0, a1)
    """

    def __init__(self, attribs):
        self.coords, self.color = attribs
        self.type = 'ga'
        self.show = True

    def __hash__(self):
        return hash(self.get_attribs())
    
    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.coords == other.coords and
                self.color == other.color)

    def __repr__(self):
        return "{} object with coordinates {}".format(self.type, self.coords)

    def get_attribs(self):
        return (self.coords, self.color)

class TX:
    """Text object initialized with a tuple of attributes.

    attribs = (coords, text, style, size, color)
    """

    def __init__(self, attribs):
        self.coords, self.text, self.style, self.size, self.color = attribs
        self.type = 'tx'
        self.show = True

    def __hash__(self):
        return hash(self.get_attribs())
    
    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.coords == other.coords and
                self.text == other.text and
                self.style == other.style and
                self.size == other.size and
                self.color == other.color)

    def __repr__(self):
        return "{} object with coordinates {}".format(self.type, self.coords)

    def get_attribs(self):
        return (self.coords, self.text, self.style, self.size, self.color)

class DL:
    """Dimension Linear object initialized with a tuple of attributes.

    attribs = (coords, color)
    coords = (p1, p2, p3, d)
    """

    def __init__(self, attribs):
        self.coords, self.color = attribs
        self.type = 'dl'
        self.show = True

    def __hash__(self):
        return hash(self.get_attribs())
    
    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.coords == other.coords and
                self.color == other.color)

    def __repr__(self):
        return "{} object with coordinates {}".format(self.type, self.coords)

    def get_attribs(self):
        return (self.coords, self.color)

if __name__ == "__main__":
    attribs = ((50,50), "this is some text", 'Verdana', 10, 'cyan',)

    t1 = TX(attribs)
    print(t1)
    print(t1.coords)
    t1.coords = (100, 100)
    print(t1.get_attribs())
    print(t1)
    
