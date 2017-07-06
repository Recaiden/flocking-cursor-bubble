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
TPS = 60/2
TICK_SPEED = 1000/TPS
DASH_FACTOR = 20
MOVEMENT_FACTOR = 2*DASH_FACTOR
DISTANCE_AVERSION = 25*25
FOCUS_ON_GOAL = 0.05*DASH_FACTOR
FOCUS_ON_COHESION = 0.05*DASH_FACTOR
FOCUS_ON_AVOIDANCE = 0.07*DASH_FACTOR

STATE_NORMAL = 0
STATE_TURN_LEFT = -1
STATE_TURN_RIGHT = 1

HIST = 3
HIST_FADE = 125

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
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.timer = QtCore.QBasicTimer()
        self.pieces = []
        
        for i in range(NUM_BIOTS):
            self.curPiece = Dasher()
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
        # only used for followers
        #xAvg = sum([piece.x for piece in self.pieces])/len(self.pieces)
        #yAvg = sum([piece.y for piece in self.pieces])/len(self.pieces)


        for piece in self.pieces:
            piece.navigate(self.target)

        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rect = self.contentsRect()

        boardTop = rect.top()
        for i, piece in enumerate(self.pieces):
            x = piece.x
            y = piece.y
            piece.draw(painter, self.target)

class Dasher(object):

    def __init__(self):
        self.state = STATE_NORMAL
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

def main():
    
    app = QtGui.QApplication(sys.argv)
    t = BiOverlay()
    t.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
