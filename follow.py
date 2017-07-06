#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division

import math
import sys, random

from ctypes import windll, Structure, c_long, byref

from PySide import QtCore, QtGui

class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]

SQUARE_SIZE = 3

NUM_BIOTS = 10
TPS = 60
TICK_SPEED = 1000/TPS
MOVEMENT_FACTOR = 2
DISTANCE_AVERSION = 25*25
FOCUS_ON_GOAL = 0.05
FOCUS_ON_COHESION = 0.05
FOCUS_ON_AVOIDANCE = 0.07

STATE_NORMAL = 0
STATE_TURN_LEFT = -1
STATE_TURN_RIGHT = 1

def queryMousePosition():
    pt = POINT()
    windll.user32.GetCursorPos(byref(pt))
    return { "x": pt.x, "y": pt.y}


class Communicate(QtCore.QObject):
    
    msgToSB = QtCore.Signal(str)

class BiOverlay(QtGui.QMainWindow):
    
    def __init__(self):
        super(BiOverlay, self).__init__()
        self.setGeometry(QtGui.QDesktopWidget().availableGeometry())

        self.setMouseTracking(True)

        self.setWindowTitle('Biot Overlay')
        self.overlay = Board(self)

        self.setCentralWidget(self.overlay)
            
        self.overlay.start()
        self.center()

        # No border
        #self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

    def center(self):
        
        screen = QtGui.QDesktopWidget().screenGeometry()
        size =  self.geometry()
        self.move((screen.width()-size.width())/2, 
            (screen.height()-size.height())/2)


class Board(QtGui.QFrame):
    
    Speed = TICK_SPEED

    def __init__(self, parent):
        super(Board, self).__init__()

        self.timer = QtCore.QBasicTimer()
        self.pieces = []
        
        for i in range(NUM_BIOTS):
            self.curPiece = Shape()
            self.curPiece.x = random.randint(0, self.frameRect().width())
            self.curPiece.y = random.randint(0, self.frameRect().height())
            self.pieces.append(self.curPiece)
            
        self.curX = 0
        self.curY = 0

        self.board = []

        self.isStarted = False
        self.isPaused = False

        self.target = QtCore.QPointF(5, 10)
        
    def start(self):
        if self.isPaused:
            return

        self.isStarted = True

        self.timer.start(Board.Speed, self)


    def pause(self):
        if not self.isStarted:
            return

        self.isPaused = not self.isPaused
        
        if self.isPaused:
            self.timer.stop()
        else:
            self.timer.start(Board.Speed, self)

        self.update()

    def keyPressEvent(self, event):
        if not self.isStarted or len(self.pieces) == 0:
            QtGui.QWidget.keyPressEvent(self, event)
            return

        key = event.key()
        
        if key == QtCore.Qt.Key_P:
            self.pause()
            return
        if self.isPaused:
            return
        elif key == QtCore.Qt.Key_D:
            self.moveTowardsTarget()
        else:
            QtGui.QWidget.keyPressEvent(self, event)

    def timerEvent(self, event):
        #print ".",

        pos = queryMousePosition()
        try:
            self.target.setX(pos["x"])
        except OverflowError as e:
            self.target.setX(0)
        try:
            self.target.setY(pos["y"])
        except OverflowError as e:
            self.target.setY(0)

        #print "(%f, %f)" %(self.curX, self.curY), "==>", "(%f, %f)" %(self.target.x(), self.target.y())
        
        if event.timerId() == self.timer.timerId():
            self.moveTowardsTarget()
        else:
            QtGui.QFrame.timerEvent(self, event)

    def moveTowardsTarget(self):
        #headings = [piece.heading for piece in self.pieces]
        xAvg = sum([piece.x for piece in self.pieces])/len(self.pieces)
        yAvg = sum([piece.y for piece in self.pieces])/len(self.pieces)

        for piece in self.pieces:
            piece.navigate(xAvg, yAvg, self.target, self.pieces)

        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rect = self.contentsRect()

        boardTop = rect.top()
        for i, piece in enumerate(self.pieces):
            x = piece.x
            y = piece.y
            self.drawSquare(painter, rect.left() + x,
                            boardTop + (y - 1),
                            i%7+1, piece.heading*180/math.pi)

    def drawSquare(self, painter, x, y, shape, angle):
        
        colorTable = [0x000000, 0xCC6666, 0x66CC66, 0x6666CC,
                      0xCCCC66, 0xCC66CC, 0x66CCCC, 0xDAAA00]

        color = QtGui.QColor(colorTable[shape])

        painter.setPen(color)

        # Circle with line pointing in the direction of travel and 2 shading arcs
        painter.drawEllipse(QtCore.QPoint(x, y), SQUARE_SIZE, SQUARE_SIZE)
        painter.drawLine(x, y,
                         x+math.cos(angle*math.pi/180)*SQUARE_SIZE, y+math.sin(angle*math.pi/180)*SQUARE_SIZE)
        painter.setPen(color.darker())
        painter.drawArc(x-SQUARE_SIZE+1, y-SQUARE_SIZE+1,
                        SQUARE_SIZE*2-2, SQUARE_SIZE*2-2,
                        (-angle+270)*16, (-180)*16)
        painter.setPen(color.lighter())
        painter.drawArc(x-SQUARE_SIZE+1, y-SQUARE_SIZE+1,
                        SQUARE_SIZE*2-2, SQUARE_SIZE*2-2,
                        (-angle+90)*16, (-180)*16)
class Shape(object):
    
    def __init__(self):
        self.state = STATE_NORMAL
        self.target = QtCore.QPointF(0, 0)
        self.x = 0
        self.y = 0
        self.xBuffer = 0
        self.yBuffer = 0
        self.heading = 0.0
        self.pieceShape = 1

        self.countOfUpdateVectorsSinceFinalizing = 0
        
    def distanceToSquare(self, other):
        return (other.x-self.x)**2+(other.y-self.y)**2

    def updateHeading(self, xn, yn, weight=0.05):
        self.xBuffer += xn*weight
        self.yBuffer += yn*weight

        self.countOfUpdateVectorsSinceFinalizing += 1

    def finalizeHeading(self):
        self.xBuffer /= self.countOfUpdateVectorsSinceFinalizing
        self.yBuffer /= self.countOfUpdateVectorsSinceFinalizing

        self.xBuffer += math.cos(self.heading)
        self.xBuffer /= 2
        self.yBuffer += math.sin(self.heading)
        self.yBuffer /= 2

        self.heading = math.atan2(self.yBuffer, self.xBuffer)
        
        self.countOfUpdateVectorsSinceFinalizing = 0
        self.xBuffer = 0#math.cos(self.heading)
        self.yBuffer = 0#math.sin(self.heading)

    def navigateToTarget(self, target):
        vectorRawX = target.x() - self.x
        vectorRawY = target.y() - self.y

        divisorUnit = math.sqrt(vectorRawX**2 + vectorRawY**2)
            
        vectorX = min(max(vectorRawX/divisorUnit, -1), 1)
        vectorY = min(max(vectorRawY/divisorUnit, -1), 1)

        # when you get too close, pick a direction to start turning away.
        # Keep turning that direction until you get far enough away again
        if self.state is STATE_NORMAL and divisorUnit <= math.sqrt(DISTANCE_AVERSION):
            self.state = random.choice([STATE_TURN_RIGHT, STATE_TURN_LEFT])
        if self.state is STATE_TURN_LEFT:
            vectorY, vectorX = vectorX, -1*vectorY
        elif self.state is STATE_TURN_RIGHT:
            vectorY, vectorX = -1*vectorX, vectorY

        self.updateHeading(vectorX, vectorY, FOCUS_ON_GOAL)

        if divisorUnit > math.sqrt(DISTANCE_AVERSION) and self.state is not STATE_NORMAL:
            self.state = STATE_NORMAL

    def navigateTowardsOthers(self, xAvg, yAvg):
        vectorRawX = xAvg - self.x
        vectorRawY = yAvg - self.y
        
        divisorUnit = math.sqrt(vectorRawX**2 + vectorRawY**2)
        
        vectorX = min(max(vectorRawX/divisorUnit, -1), 1)
        vectorY = min(max(vectorRawY/divisorUnit, -1), 1)
        
        self.updateHeading(vectorX, vectorY, FOCUS_ON_COHESION)

    def navigateClear(self, obstacles):
        vectorXAversion = 0
        vectorYAversion = 0
        vectorX = 0
        vectorY = 0
        for pieceOther in obstacles:
            if pieceOther is self:
                continue
            d = self.distanceToSquare(pieceOther)
            if d > DISTANCE_AVERSION:
                continue
            vectorRawX = (self.x - pieceOther.x)
            vectorRawY = (self.y - pieceOther.y)

            divisorUnit = math.sqrt(vectorRawX**2 + vectorRawY**2)
            
            vectorX = min(max(vectorRawX/divisorUnit, -1), 1)
            vectorY = min(max(vectorRawY/divisorUnit, -1), 1)
            
            vectorXAversion += vectorX
            vectorYAversion += vectorY
        self.updateHeading(vectorX, vectorY, FOCUS_ON_AVOIDANCE)

    def navigate(self, xAvg, yAvg, target, others):
        # Towards other boids
        self.navigateTowardsOthers(xAvg, yAvg)
        
        # Towards target, but don't ram it
        self.navigateToTarget(target)
        
        # Aversion
        self.navigateClear(others)
        
        # Gather and go
        self.finalizeHeading()
        
        self.xOld = self.x
        self.yOld = self.y
        self.x += math.cos(self.heading)*MOVEMENT_FACTOR
        self.y += math.sin(self.heading)*MOVEMENT_FACTOR

def main():
    
    app = QtGui.QApplication(sys.argv)
    t = BiOverlay()
    t.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
