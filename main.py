##### My Libs #####
import utils
import supportClasses

##### Window Libs #####
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
import win32gui
import win32con
import win32api
import sys
import os

##### Logic Libs #####
import math
import random
import time
import json


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.sprites = []
        self.load()

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
    
    def getDataPath(self):
        return os.path.join(os.environ['APPDATA'], 'DeskMeadow')

    def save(self):
        flowerDict = []
        for sprite in self.sprites:
            if isinstance(sprite, Flower):
                flowerDict.append({
                    'spriteid': sprite.id,
                    'timeBorn': sprite.timeBorn,
                    'colour': sprite.colour,
                    'petalWidth': sprite.petalWidth,
                    'petalSize': sprite.petalSize,
                    'petalOffset': sprite.petalOffset,
                    'numPetals': sprite.numPetals,
                    'centreColour': sprite.centreColour,
                    'lengths': sprite.lengths,
                    'angles': sprite.angles,
                    'nodes': sprite.nodes,
                    'nodeLength': sprite.nodeLength,
                    'stalkThickness': sprite.stalkThickness,
                    'stage': sprite.stage,
                    'pos': sprite.position,
                    'points': sprite.points,
                    'leafAngles': sprite.leafAngles,
                    'growthMultiplier': sprite.growthMultiplier
                })
            elif isinstance(sprite, SeedBag):
                seedBag = sprite
        flowerDict.append({
            'timeAtLastSave': time.time(),
            'seedCount': seedBag.seedCount
        })

        with open(os.path.join(self.getDataPath(), 'flowerData.json'), 'w') as f:
            jsonObj = json.dumps(flowerDict, indent=4)
            f.write(jsonObj)
    
    def load(self):
        try:
            with open(os.path.join(self.getDataPath(), 'flowerData.json'), 'r') as f:
                flowerData = list(json.load(f))
        except FileNotFoundError:
            os.makedirs(self.getDataPath(), exist_ok=True)
            with open(os.path.join(self.getDataPath(), 'flowerData.json'), 'w') as f:
                json.dump([], f)
                flowerData = []
        
        metaData = None
        if len(flowerData) != 0:
            metaData = flowerData.pop()
            timeSinceSave = time.time()-metaData['timeAtLastSave']
        else:
            timeSinceSave = 0
        
        for flower in flowerData:
            flower['window'] = self
            self.sprites.append(Flower(**flower))
            self.sprites[-1].catchup(timeSinceSave)
        
        if metaData is None:
            self.sprites.append(SeedBag(window=self, pos=(500, 500)))
        else:
            self.sprites.append(SeedBag(window=self, pos=(500, 500), seedCount=metaData['seedCount']+timeSinceSave//17280, secondsSinceRefill=timeSinceSave%17280))
    
    def updateScr(self):
        self.frame += 1
        for sprite in self.sprites:
            for child in sprite.children:
                if self.frame%max(1, self.FPS//child.updatesPerSecond) == 0:
                    child.update()
            if self.frame%max(1, self.FPS//sprite.updatesPerSecond) == 0:
                sprite.update()
                if sprite.dead:
                    if isinstance(sprite, Seed):
                        taskbar_handle = win32gui.FindWindow("Shell_TrayWnd", None)
                        rect = win32gui.GetWindowRect(taskbar_handle)
                        self.sprites.append(Flower(window=self, pos=(sprite.position[0], rect[1])))
                    self.sprites.remove(sprite)
            
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(Qt.green)
        pen.setWidth(3)
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
    def __init__(self, window, pos, seedCount=None, secondsSinceRefill=None):
        super().__init__(window=window, pos=pos, image='sprites/seedBag.png', holdable=True, size=64)
        self.lastPlantedSeed = 100
        self.seedCount = 5 if seedCount is None else seedCount
        self.secondsSinceRefill = 0 if secondsSinceRefill is None else secondsSinceRefill
    
    def onHold(self, oldPos, newPos):
        if abs(oldPos[1]-newPos[1]) > 2 and self.lastPlantedSeed > 0.3 and self.seedCount != 0:
            self.lastPlantedSeed = 0
            self.seedCount -= 1
            self.window.sprites.append(Seed(window=self.window, pos=self.position))

    def update(self):
        self.lastPlantedSeed += 1/self.updatesPerSecond
        
        self.secondsSinceRefill += 1/self.updatesPerSecond
        if self.secondsSinceRefill >= 17280:
            self.setImage('sprites/seedBag.png')
            self.seedCount += 1
            self.secondsSinceRefill = 0
        
        if self.seedCount == 0:
            self.setImage('sprites/seedBagEmpty.png')
            

class Seed(supportClasses.Sprite):
    def __init__(self, window, pos):
        super().__init__(window=window, pos=pos, shape=supportClasses.Shape('ellipse', 10, 10, (0, 128, 0), (0, 128, 0)))

        initMaxSpeed = 100
        self.velocity = ((random.random()-0.5)*(initMaxSpeed*2), -random.random()*initMaxSpeed)
    
    def update(self):
        self.velocity = (self.velocity[0], self.velocity[1]+500/self.updatesPerSecond)
        self.realPos = (self.realPos[0]+(self.velocity[0]/self.updatesPerSecond), self.realPos[1]+(self.velocity[1]/self.updatesPerSecond))
        if self.x < 0 or self.x > win32api.GetSystemMetrics(0):
            self.velocity = (-self.velocity[0], self.velocity[1])

    @property
    def dead(self):
        taskbar_handle = win32gui.FindWindow("Shell_TrayWnd", None)
        rect = win32gui.GetWindowRect(taskbar_handle)
        return self.y > rect[1]

class Flower(supportClasses.Sprite):
    def __init__(self, window, pos, spriteid=None, timeBorn=None, growthMultiplier=None, nodes=None, stage=None, nodeLength=None, angles=None, lengths=None, stalkThickness=None, points=None, leafAngles=None, petalSize=None, petalWidth=None, numPetals=None, petalOffset=None, colour=None, centreColour=None):
        super().__init__(window=window, pos=pos, spriteid=spriteid)

        self.timeBorn = time.time() if timeBorn is None else timeBorn
        self.growthMultiplier = (random.random()+1)*0.0007 if growthMultiplier is None else growthMultiplier

        self.nodes = random.randint(1, 3) if nodes is None else nodes
        self.stage = 1 if stage is None else stage
        self.nodeLength = 0 if nodeLength is None else nodeLength
        self.angles = [] if angles is None else angles
        self.lengths = [] if lengths is None else lengths
        self.stalkThickness = random.randint(3, 5) if stalkThickness is None else stalkThickness
        if points is None or angles == [] or lengths == []:
            self.angles = []
            self.lengths = []
            self.points = [self.position]
            for i in range(self.nodes):
                self.angles.append(random.uniform(-math.pi/6, math.pi/6))
                self.lengths.append(random.uniform(30, 60))
                self.points.append((round(self.points[-1][0]+self.lengths[-1]*math.sin(self.angles[-1])), round(self.points[-1][1]-self.lengths[-1]*math.cos(self.angles[-1]))))
        else:
            self.points = points
            
        if leafAngles is None:
            self.leafAngles = []
            for i in range(self.nodes-1):
                self.leafAngles.append([])
                for j in range(random.randint(1, 4)):
                    self.leafAngles[-1].append(random.choice([random.randint(60, 120), random.randint(-120, -60)]))
        else:
            self.leafAngles = leafAngles

        self.petalSize = random.randint(10, 30) if petalSize is None else petalSize
        self.petalWidth = random.randint(1, 10) if petalWidth is None else petalWidth
        self.numPetals = random.randint(3, 20) if numPetals is None else numPetals
        self.petalOffset = random.randint(0, 30) if petalOffset is None else petalOffset
        self.colour = (random.randint(64, 255), random.randint(0, 255), random.randint(64, 255)) if colour is None else colour

        self.centreColour = (random.randint(64, 255), random.randint(0, 255), random.randint(64, 255)) if centreColour is None else centreColour

    def update(self):
        if self.stage != self.nodes+1:
            self.nodeLength += self.growthMultiplier/self.updatesPerSecond
            if self.nodeLength >= self.lengths[self.stage-1]:
                self.stage += 1
                self.nodeLength = 0
    
    def catchup(self, timeSinceSave, skip=5):
        for i in range(round(timeSinceSave)):
            if self.stage != self.nodes+1:
                self.nodeLength += self.growthMultiplier/(1/skip)
                if self.nodeLength >= self.lengths[self.stage-1]:
                    self.stage += 1
                    self.nodeLength = 0
            else:
                break
    
    def draw(self, painter):
        pen = QPen(QColor(0, 128, 0))
        pen.setWidth(self.stalkThickness)
        brush = QBrush(QColor(0, 128, 0))
        painter.setPen(pen)
        painter.setBrush(brush)

        for i in range(self.stage):
            if i == self.stage-1 and self.stage != self.nodes+1:
                painter.drawLine(self.points[i][0], self.points[i][1], round(self.points[i][0]+self.nodeLength*math.sin(self.angles[i])), round(self.points[i][1]-self.nodeLength*math.cos(self.angles[i])))
            elif i != self.nodes:
                painter.drawLine(self.points[i][0], self.points[i][1], self.points[i+1][0], self.points[i+1][1])

                if i != self.nodes-1:
                    for j in range(len(self.leafAngles[i])):
                        painter.save()
                        painter.translate(self.points[i+1][0], self.points[i+1][1])
                        painter.rotate(self.leafAngles[i][j])
                        painter.drawEllipse(0, 0, 8, 20)
                        painter.restore()
                else:
                    for j in range(self.numPetals):
                        pen = QPen(QColor(*self.colour))
                        pen.setWidth(3)
                        brush = QBrush(QColor(*self.colour))
                        painter.setPen(pen)
                        painter.setBrush(brush)

                        painter.save()
                        painter.translate(self.points[-1][0], self.points[-1][1])
                        painter.rotate(j*360/self.numPetals+self.petalOffset)
                        painter.drawEllipse(0, 0, self.petalWidth, self.petalSize)
                        painter.restore()
                    
                    pen = QPen(QColor(*self.centreColour))
                    pen.setWidth(3)
                    brush = QBrush(QColor(*self.centreColour))
                    painter.setPen(pen)
                    painter.setBrush(brush)

                    painter.drawEllipse(self.points[-1][0]-self.petalSize//4, self.points[-1][1]-self.petalSize//4, self.petalSize//2, self.petalSize//2)

    @property
    def age(self):
        return time.time() - self.timeBorn

    @property
    def dead(self):
        return self.age > 7*24*60*60

def main():
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()