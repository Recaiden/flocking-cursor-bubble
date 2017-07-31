from PySide import QtCore, QtGui

import math, random

STATE_NORMAL = 0
STATE_TURN_LEFT = -1
STATE_TURN_RIGHT = 1

# These control the flgiht patterns.
# None (all low) = they swoop around mostly ignoring each other.  Desired pattern.
# Cohesion = they form into a tight coil and eventually cohere into a tight ball that tracks the target all together, only breaking apart once it has sailed far offscreen, where the process repeats.  It may close into a swirl around wth cursor without cohering.  Complex but visually boring
# Avoidance = Followers 'bounce' off of each other, producing large course changes.  Desired pattern.
# Goal =  they swarm onto the target very tightly and then coil around it.
# Goal + Avoidance = As Goal, but 'bouncier'
# Cohesion + Avoidance =  a bumbling tangle that only very slowly approaches the taget.
# Goal + Cohesion = a near-perfect circle right around the target
# Goal + Cohesion + Avoidance = Erratic, jumpy pattern that converges to a coil around the target
FOCUS_ON_GOAL = 0.05
FOCUS_ON_COHESION = 0.05
FOCUS_ON_AVOIDANCE = 0.7

DISTANCE_ROOT = 25
DISTANCE_AVERSION = DISTANCE_ROOT**2

MOVEMENT_FACTOR = 2
SQUARE_SIZE = 3

colorTable = [0x101010, 0xCC6666, 0x66CC66, 0x6666CC,
                      0xCCCC66, 0xCC66CC, 0x66CCCC, 0xDAAA00]

class Follower(object):
    
    def __init__(self):
        self.state = STATE_NORMAL
        self.target = QtCore.QPointF(0, 0)
        self.x = 0
        self.y = 0
        self.xBuffer = 0
        self.yBuffer = 0
        self.heading = 0.0

        self.color = QtGui.QColor(random.choice(colorTable))

        self.countOfUpdateVectorsSinceFinalizing = 0
        
    def distanceToSquare(self, other):
        return (other.x-self.x)**2 + (other.y-self.y)**2

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
        if self.state is STATE_NORMAL and divisorUnit <= DISTANCE_ROOT:
            self.state = random.choice((STATE_TURN_RIGHT, STATE_TURN_LEFT))
        if self.state is STATE_TURN_LEFT:
            vectorY, vectorX = vectorX, -1*vectorY
        elif self.state is STATE_TURN_RIGHT:
            vectorY, vectorX = -1*vectorX, vectorY

        self.updateHeading(vectorX, vectorY, FOCUS_ON_GOAL)

        if divisorUnit > DISTANCE_ROOT and self.state is not STATE_NORMAL:
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
        clearing = False
        for pieceOther in obstacles:
            if pieceOther is self:
                continue
            if abs(pieceOther.x - self.x) > DISTANCE_AVERSION or abs(pieceOther.y - self.y) > DISTANCE_AVERSION:
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
            clearing = True
        if clearing:
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

    def draw(self, painter, target):
        color = self.color
        x = self.x
        y = self.y
        angle = self.heading
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

        
