import utils
import uuid
from PyQt5.QtGui import QPen, QBrush, QColor

class Sprite:
    def __init__(self, window=None, pos=None, spriteid=None, image=None, shape=None, size=32, holdable=False, updatesPerSecond=60):
        self.window = window
        if spriteid is None:
            spriteid = uuid.uuid4()
        self.id = str(spriteid)
        self.held = False
        self.holdable = holdable
        self.updatesPerSecond = updatesPerSecond
        self.image = utils.scaleImage(image, size)
        self.shape = shape
        if pos is None:
            pos = (0, 0)
        self.realPos = pos
        self.size = size
        self.children = []
    
    def getChildren(self):
        return self.children
    
    def update(self):
        pass

    def onClick(self):
        pass

    def onHold(self, oldPos, newPos):
        pass

    def draw(self, painter):
        if self.image != None:
            painter.drawPixmap(self.x, self.y, self.image)
        elif self.shape != None:
            pen = QPen(QColor(*self.shape.outlineColour))
            pen.setWidth(3)
            brush = QBrush(QColor(*self.shape.colour))
            painter.setPen(pen)
            painter.setBrush(brush)

            if self.shape.name == 'ellipse':
                painter.drawEllipse(self.x, self.y, self.shape.width, self.shape.height)
            elif self.shape.name == 'rectangle':
                painter.drawRect(self.x, self.y, self.shape.width, self.shape.height)
    
    def move(self, pos):
        self.realPos = pos
    
    def setImage(self, newImage):
        self.image = utils.scaleImage(newImage, self.size)

    @property
    def dead(self):
        return False

    @property
    def realx(self):
        return self.realPos[0]
    
    @property
    def realy(self):
        return self.realPos[1]
    
    @property
    def x(self):
        return self.position[0]
    
    @property
    def y(self):
        return self.position[1]
    
    @property
    def position(self):
        return (round(self.realPos[0]), round(self.realPos[1]))
    
class Shape:
    def __init__(self, name, width, height, colour, outlineColour):
        self.name = name
        self.width = width
        self.height = height
        self.colour = colour
        self.outlineColour = outlineColour