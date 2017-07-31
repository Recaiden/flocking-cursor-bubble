from PySide import QtCore, QtGui

import math, random

HIST = 3
HIST_FADE = 125
DISTANCE_AVERSION = 25*25

class Dasher(object):
    def __init__(self):
        self.target = QtCore.QPointF(0, 0)
        self.x = 0
        self.y = 0
        self.xOld = 0
        self.yOld = 0
        self.xPlace = [0]*HIST
        self.yPlace = [0]*HIST
        self.pointer = 0
        self.color = QtGui.QColor(random.choice([0x000000, 0xCC6666, 0x66CC66, 0x6666CC,
                      0xCCCC66, 0xCC66CC, 0x66CCCC, 0xDAAA00]))

        self.countOfUpdateVectorsSinceFinalizing = 0
        
    def distanceToSquare(self, other):
        return (other.x-self.x)**2+(other.y-self.y)**2

    def crossesCenter(self, target, radius):
        p1 = (self.xPlace[self.pointer], self.yPlace[self.pointer])
        p2 = (self.xPlace[self.pointer-1], self.yPlace[self.pointer-1])
        c = (target.x()-32, target.y())
        dist = math.sqrt((p2[0] - p1[0])*(p2[0] - p1[0]) + (p2[1] - p1[1])*(p2[1] - p1[1]))

        if dist:
            distMin = abs(((c[0] - p1[0]) * (p2[1] - p1[1]) - (c[1] - p1[1]) * (p2[0] - p1[0])) / dist)
            if distMin <= radius:
                return True
        return False


    def navigate(self, target):
        self.xOld = self.x
        self.yOld = self.y

        self.pointer = (self.pointer + 1) % HIST        

        # Only try ten times to find a nice route.  Could otherwise hang with long movements
        x = 50
        while x:
            heading = random.randint(0, 360)*math.pi/180
            self.xPlace[self.pointer] = target.x() - 32 + math.cos(heading)*DISTANCE_AVERSION/10
            self.yPlace[self.pointer] = target.y() + math.sin(heading)*DISTANCE_AVERSION/10
            #self.x = target.x() + math.cos(heading)*DISTANCE_AVERSION/10-32
            #self.y = target.y() + math.sin(heading)*DISTANCE_AVERSION/10
            if not self.crossesCenter(target, 15):
                break
            x-= 1

    def draw(self, painter, target):
        color = self.color
        painter.setPen(color)
        for i in range(len(self.xPlace)):
            idx = (self.pointer+i) % HIST
            painter.drawLine(self.xPlace[idx], self.yPlace[idx],
                             self.xPlace[idx-1], self.yPlace[idx-1])
            color = color.lighter(HIST_FADE)
            painter.setPen(color)
        #painter.drawLine(self.x, self.y, self.xOld, self.yOld)
