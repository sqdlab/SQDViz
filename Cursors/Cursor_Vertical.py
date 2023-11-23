import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import functions as fn

class Cursor_Vertical(pg.GraphicsObject):
    """
    **Bases:** :class:`GraphicsObject <pyqtgraph.GraphicsObject>`
    
    Used for marking a horizontal or vertical region in plots.
    The region can be dragged and is bounded by lines which can be dragged individually.
    
    ===============================  =============================================================================
    **Signals:**
    sigRegionChangeFinished(self)    Emitted when the user has finished dragging the region (or one of its lines)
                                     and when the region is changed programatically.
    sigRegionChanged(self)           Emitted while the user is dragging the region (or one of its lines)
                                     and when the region is changed programatically.
    ===============================  =============================================================================
    """
    
    sigRegionChangeFinished = QtCore.Signal(object)
    sigRegionChanged = QtCore.Signal(object)
    
    def __init__(self, x, line_colour, callback_bounds):
        pg.GraphicsObject.__init__(self)
        self.blockLineSignal = False
        self.moving = False
        self.mouseHovering = False

        self._boundingRectCache = None

        penBase = pg.mkPen(line_colour)
        h,s,v = penBase.color().hue(), penBase.color().saturation(), penBase.color().value()
        invcol = [((h + 128) % 255)/255.0, s/255.0, v/255.0]
        #
        lineKwds = dict(
            movable=True,
            pen=penBase,
            hoverPen=pg.mkPen(QtGui.QColor.fromHsvF(*invcol)),
        )
        self.line = pg.InfiniteLine(QtCore.QPointF(x, 0), angle=90, **lineKwds)
        #
        self.line.setParentItem(self)
        self.line.sigPositionChangeFinished.connect(self.lineMoveFinished)
        self.line.sigPositionChanged.connect(self.lineMoved)

        self._callback_bounds = callback_bounds

        self.setAcceptHoverEvents(True)

    def onPointsClicked(self, points):
        print('Ain\'t getting individual points ', points)
        points.setPen('b', width=2)

    def boundingRect(self):
        br = QtCore.QRectF(self.viewRect())  # bounds of containing ViewBox mapped to local coords.

        rng = self.get_value()
        br.setLeft(rng)
        br.setRight(rng)
        length = br.height()
        br.setBottom(br.top() + length)
        br.setTop(br.top())

        br = br.normalized()
        
        if self._boundingRectCache != br:
            self._boundingRectCache = br
            self.prepareGeometryChange()
        
        return br
        
    def paint(self, p, *args):
        pass

    def lineMoved(self):
        if self.blockLineSignal:
            return
        self.prepareGeometryChange()

    def lineMoveFinished(self):
        self.sigRegionChangeFinished.emit(self)
    
    def get_value(self):
        return self.line.value()
    
    def set_value(self, x):
        zMin, zMax = self._callback_bounds()
        if x < zMin:
            x = zMin
        elif x > zMax:
            x = zMax        
        self.line.setValue(x)

