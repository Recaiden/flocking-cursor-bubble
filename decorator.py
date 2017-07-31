#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division

from dasher import Dasher
from follower import Follower
from orbiter import Orbiter
from orbiter import sol

import math
import sys, random

from ctypes import windll, Structure, c_long, byref

from PySide import QtCore, QtGui

class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]

NUM_BIOTS = 8
TPS = 60
TICK_SPEED = 1000/TPS

def queryMousePosition():
    pt = POINT()
    windll.user32.GetCursorPos(byref(pt))
    return { "x": pt.x, "y": pt.y}


class Communicate(QtCore.QObject):
    
    msgToSB = QtCore.Signal(str)

class BiOverlay(QtGui.QMainWindow):
    
    def __init__(self):
        super(BiOverlay, self).__init__()

        desktop = QtGui.QApplication.desktop()
        cScreens = desktop.screenCount()

        if cScreens == 1:
            self.setGeometry(QtGui.QDesktopWidget().availableGeometry())
        elif cScreens == 2:
            self.setGeometry(desktop.availableGeometry(0).united(desktop.availableGeometry(1)))
        else:
            rect = desktop.availableGeometry(0)
            for i in range(1, cScreens):
                rect = rect.united(desktop.availableGeometry(i))
            self.setGeometry(rect)

        self.offset = self.geometry().left()

        self.setMouseTracking(True)

        self.setWindowTitle('Biot Overlay')
        self.overlay = Board(self)

        self.setCentralWidget(self.overlay)
            
        self.overlay.start()

        # No border
        #self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        

class Board(QtGui.QFrame):
    Speed = TICK_SPEED

    def __init__(self, parent):
        super(Board, self).__init__()
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.timer = QtCore.QBasicTimer()
        self.pieces = []
        
        for i in range(NUM_BIOTS):
            #self.curPiece = Dasher()
            #self.curPiece = Orbiter()
            self.curPiece = Follower()
            self.curPiece.x = random.randint(0, self.frameRect().width())
            self.curPiece.y = random.randint(0, self.frameRect().height())
            self.pieces.append(self.curPiece)
        #self.pieces = sol
            
        self.curX = 0
        self.curY = 0

        self.offset = parent.offset

        self.target = QtCore.QPointF(5, 10)
        
    def start(self):
        self.timer.start(Board.Speed, self)

    def timerEvent(self, event):
        #print ".",

        pos = queryMousePosition()
        try:
            self.target.setX(pos["x"] - self.offset)
        except OverflowError as e:
            self.target.setX(0)
        try:
            self.target.setY(pos["y"])
        except OverflowError as e:
            self.target.setY(0)

        if event.timerId() == self.timer.timerId():
            self.moveTowardsTarget()
        else:
            QtGui.QFrame.timerEvent(self, event)

    def moveTowardsTarget(self):
        # only used for followers
        xAvg = sum([piece.x for piece in self.pieces])/len(self.pieces)
        yAvg = sum([piece.y for piece in self.pieces])/len(self.pieces)


        for piece in self.pieces:
            piece.navigate(xAvg, yAvg, self.target, self.pieces)

        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        for i, piece in enumerate(self.pieces):
            piece.draw(painter, self.target)

def main():
    
    app = QtGui.QApplication(sys.argv)
    t = BiOverlay()
    t.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
