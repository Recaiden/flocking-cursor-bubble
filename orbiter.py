from PySide import QtCore, QtGui

import math, random

DISTANCE_AVERSION = 25*25

class Orbiter(object):
    def __init__(self, rateOrbital=None, sizePlanet=3, widthX=None, widthY=None ):
        self.target = QtCore.QPointF(0, 0)
        self.angle = random.randint(0, 5760) #16ths of a degree
        self.widthMajor = random.randint(0, 100) if widthX is None else widthX
        self.widthMinor = self.widthMajor + random.randint(-5, 5) if widthY is None else widthY
        self.rate = random.choice((.25, .5, 1, 1.25, 1.5, 2, 3, 5)) if rateOrbital is None else rateOrbital
        self.size = sizePlanet
        self.color = QtGui.QColor(random.choice([0x000000, 0xCC6666, 0x66CC66, 0x6666CC,
                      0xCCCC66, 0xCC66CC, 0x66CCCC, 0xDAAA00]))
        
    def navigate(self, target):
        self.target = target
        self.angle = (self.angle + 16* self.rate)%5760

    def draw(self, painter, target):
        color = self.color
        painter.setPen(color)

        focus = self.target + QtCore.QPointF(-65, 0)
        
        painter.drawEllipse(focus, 1.0*self.widthMajor, 1.0*self.widthMinor)

        x = self.target.x()-65 + self.widthMajor*math.cos(self.angle/16*math.pi/180)
        y = self.target.y() + self.widthMinor*math.sin(self.angle/16*math.pi/180)

        painter.drawEllipse(QtCore.QPoint(x, y), self.size, self.size)

        
        #painter.drawLine(self.x, self.y, self.xOld, self.yOld)

pEarth = Orbiter(1, 3, 76, 75)
pEarth.color = QtGui.QColor(0x00FFFF)
pMercury = Orbiter(4, 1, 29, 28)
pMercury.color = QtGui.QColor(0xFFAA00)
pVenus = Orbiter(1.5, 3, 53, 53)
pVenus.color = QtGui.QColor(0x55AA00)
pMars = Orbiter(1, 2, 100, 99)
pMars.color = QtGui.QColor(0xFFAAAA)

pJupiter = Orbiter(.09, 10, 195, 195)
pJupiter.color = QtGui.QColor(0xC99039)
pSaturn = Orbiter(.03, 9, 253, 253)
pSaturn.color = QtGui.QColor(0x9D3C55)
pUranus = Orbiter(.01, 6, 327, 327)
pUranus.color = QtGui.QColor(0x0055FF)
pNeptune = Orbiter(.007, 5, 382, 382)
pNeptune.color = QtGui.QColor(0x00AAFF)

sol = (pMercury, pVenus, pEarth, pMars, pJupiter, pSaturn, pUranus, pNeptune)


