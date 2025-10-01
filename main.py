##### My Libs #####
import utils
import supportClasses

##### Window Libs #####
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QPen, QBrush, QImage, QColor
import win32gui
import win32con
import win32api
import sys

##### Logic Libs #####
import math
import random


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.sprites = []

        ## V Meadow Specific V ##

        self.sprites.append(SeedBag(self, (500, 500)))

        ## ^ Meadow Specific ^ ##

        self.mousePressed = False
        self.heldSprite = None
        self.heldSpriteOffset = (0, 0)

        self.frame = 0
        self.FPS = 120
        self.updateTimer = QTimer(self)
        self.updateTimer.timeout.connect(self.updateScr)
        self.updateTimer.start(1000//self.FPS)

        self.autosaveTimer = QTimer(self)
        self.autosaveTimer.timeout.connect(self.save)
        self.autosaveTimer.start(10000)

    def initUI(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint | # todo: change to bottom after development
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Make window click-through
        hwnd = self.winId().__int__()
        win32gui.SetWindowLong(
            hwnd,
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED # | win32con.WS_EX_TRANSPARENT
        )
        
        # Set window size to be full screen
        self.setGeometry(0, 0, win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1))
        self.show()
    
    def save(self):
        return
    
    def updateScr(self):
        self.frame += 1
        for sprite in self.sprites:
            for child in sprite.children:
                if self.frame%max(1, self.FPS//child.updatesPerSecond) == 0:
                    child.update()
            if self.frame%max(1, self.FPS//sprite.updatesPerSecond) == 0:
                sprite.update()
                if sprite.dead:
                    self.sprites.append(Flower(self, (sprite.position[0], 1130)))
                    self.sprites.remove(sprite)
            
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(Qt.green)
        brush = QBrush(QColor(Qt.green))
        painter.setPen(pen)
        painter.setBrush(brush)
        
        for sprite in self.sprites:
            for child in sprite.children: # todo: intro layers for foreground/background objs
                child.draw(painter)
            sprite.draw(painter)
    
    def mousePressEvent(self, event):
        self.mousePressed = True
    
    def mouseMoveEvent(self, event):
        if self.mousePressed and self.heldSprite == None:
            for sprite in self.sprites:
                if sprite.holdable:
                    if (sprite.x <= event.x() <= sprite.x + sprite.size and 
                        sprite.y <= event.y() <= sprite.y + sprite.size):
                        self.heldSprite = sprite
                        sprite.held = True
                        self.heldSpriteOffset = (sprite.x-event.x(), sprite.y-event.y())
                        break
                for child in sprite.children:
                    if child.holdable:
                        if (child.x <= event.x() <= child.x + child.size and 
                            child.y <= event.y() <= child.y + child.size):
                            self.heldSprite = child
                            child.held = True
                            self.heldSpriteOffset = (child.x-event.x(), child.y-event.y())
                            break
        elif self.mousePressed:
            oldPos = self.heldSprite.position
            self.heldSprite.move((event.x()+self.heldSpriteOffset[0], event.y()+self.heldSpriteOffset[1]))
            newPos = self.heldSprite.position
            self.heldSprite.onHold(oldPos, newPos)
    
    def mouseReleaseEvent(self, event):
        self.mousePressed = False
        if self.heldSprite != None:
            self.heldSprite.held = False
        ############### todo: remove and use seed bag ###############
        else:
            self.sprites.append(Seed(self, (event.x(), event.y())))
        self.heldSprite = None
        for sprite in self.sprites:
            if (sprite.x <= event.x() <= sprite.x + sprite.size and 
                sprite.y <= event.y() <= sprite.y + sprite.size):
                sprite.onClick()
                break
            for child in sprite.children:
                if (child.x <= event.x() <= child.x + child.size and 
                    child.y <= event.y() <= child.y + child.size):
                    child.onClick()
                    break

class SeedBag(supportClasses.Sprite):
    def __init__(self, window, pos):
        super().__init__(window, pos, image='sprites/seeds.png', holdable=True)
        self.secondsSinceLastSeed = 100
    
    def onHold(self, oldPos, newPos):
        if abs(oldPos[1]-newPos[1]) > 2 and self.secondsSinceLastSeed > 0:
            self.secondsSinceLastSeed = 0
            self.window.sprites.append(Seed(self.window, self.position))

    def update(self):
        self.secondsSinceLastSeed += 1/self.updatesPerSecond

class Seed(supportClasses.Sprite):
    def __init__(self, window, pos):
        super().__init__(window, pos, shape=supportClasses.Shape('ellipse', 10, 10))

        initMaxSpeed = 100
        self.velocity = ((random.random()-0.5)*(initMaxSpeed*2), -random.random()*initMaxSpeed)
    
    def update(self):
        self.velocity = (self.velocity[0], self.velocity[1]+500/self.updatesPerSecond)
        self.realPos = (self.realPos[0]+(self.velocity[0]/self.updatesPerSecond), self.realPos[1]+(self.velocity[1]/self.updatesPerSecond))
        if self.x < 0 or self.x > win32api.GetSystemMetrics(0):
            self.velocity = (-self.velocity[0], self.velocity[1])

    @property
    def dead(self):
        return self.y > win32api.GetSystemMetrics(1)

class Flower(supportClasses.Sprite):
    def __init__(self, window, pos):
        super().__init__(window, pos)

        self.age = 0
        self.growthMultiplier = (random.random()+1)*5

        self.nodes = 3#random.randint(1, 3)
        self.stage = self.nodes
        self.nodeLength = 0
        self.lengths = [random.uniform(10, 50)]
        self.angles = [0]
        self.points = [self.position]
        for i in range(self.nodes):
            self.angles.append(random.uniform(math.pi/6, 2*math.pi/3))
            self.points.append((self.points[-1][0]+self.lengths[-1]*math.cos(self.angles[-1]), self.points[-1][1]-self.lengths[-1]*math.sin(self.angles[-1])))
            self.lengths.append(random.uniform(10, 50))

    def update(self):
        self.age += 1/self.updatesPerSecond
        self.nodeLength += self.growthMultiplier/self.updatesPerSecond
    
    def draw(self, painter):
        for i in range(self.stage):
            painter.drawLine(round(self.points[i][0]), round(self.points[i][1]), round(self.points[i+1][0]), round(self.points[i+1][1]))
    


def main():
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()