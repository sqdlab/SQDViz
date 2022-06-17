import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import functions as fn

class Cursor_Cross(pg.GraphicsObject):
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
    sigChangedCurX = QtCore.Signal(object)
    sigChangedCurY = QtCore.Signal(object)
    
    def __init__(self, x, y, line_colour, brush=None, hoverBrush=None):        
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
        self.lines = [pg.InfiniteLine(QtCore.QPointF(x, 0), angle=90, **lineKwds), pg.InfiniteLine(QtCore.QPointF(0, y), angle=0, **lineKwds)]
        #
        for l in self.lines:
            l.setParentItem(self)
            l.sigPositionChangeFinished.connect(self.lineMoveFinished)
        self.lines[0].sigPositionChanged.connect(self._line0Moved)
        self.lines[1].sigPositionChanged.connect(self._line1Moved)
            
        if brush is None:
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 255, 50))
        self.setBrush(brush)
        
        if hoverBrush is None:
            c = self.brush.color()
            c.setAlpha(min(c.alpha() * 2, 255))
            hoverBrush = fn.mkBrush(c)
        self.setHoverBrush(hoverBrush)

        self.setAcceptHoverEvents(True)

    def connect_plt_to_move_event(self, plt_canvas):
        plt_canvas.scene().sigMouseMoved.connect(self.mouseMoved)

    def release_from_plots(self):
        self.sigChangedCurX.disconnect()
        self.sigChangedCurY.disconnect()

    def mouseMoved(self,evt):
        pt_mouse = self.mapFromDevice(evt)
        if pt_mouse == None:
            return
        rect_centre = self.boundingRect()
        pt_inside_centre = rect_centre.contains(pt_mouse)
        for l in self.lines:
            l.setMovable(not pt_inside_centre)

    def onPointsClicked(self, points):
        print('Ain\'t getting individual points ', points)
        points.setPen('b', width=2) 

    def setBrush(self, *br, **kargs):
        """Set the brush that fills the region. Can have any arguments that are valid
        for :func:`mkBrush <pyqtgraph.mkBrush>`.
        """
        self.brush = fn.mkBrush(*br, **kargs)
        self.currentBrush = self.brush

    def setHoverBrush(self, *br, **kargs):
        """Set the brush that fills the region when the mouse is hovering over.
        Can have any arguments that are valid
        for :func:`mkBrush <pyqtgraph.mkBrush>`.
        """
        self.hoverBrush = fn.mkBrush(*br, **kargs)

    def boundingRect(self):
        br = QtCore.QRectF(self.viewRect())  # bounds of containing ViewBox mapped to local coords.

        nominalBoxSizePx = 20
        #
        lenX = self.pixelLength(pg.Point([1,0])) * nominalBoxSizePx
        lenY = self.pixelLength(pg.Point([0,1])) * nominalBoxSizePx

        br.setTop(self.lines[1].value()+lenY*0.5)
        br.setBottom(self.lines[1].value()-lenY*0.5)
        br.setLeft(self.lines[0].value()-lenX*0.5)
        br.setRight(self.lines[0].value()+lenX*0.5)

        br = br.normalized()
        
        if self._boundingRectCache != br:
            self._boundingRectCache = br
            self.prepareGeometryChange()
        
        return br
        
    def paint(self, p, *args):
        p.setBrush(self.currentBrush)
        p.setPen(fn.mkPen(None))
        p.drawRect(self.boundingRect())

    def dataBounds(self, axis, frac=1.0, orthoRange=None):
        return None

    def lineMoved(self, i):
        if self.blockLineSignal:
            return
        
        self.prepareGeometryChange()
        if i == 0:
            self.sigChangedCurX.emit(self)
        else:
            self.sigChangedCurY.emit(self)

    def _line0Moved(self):
        self.lineMoved(0)

    def _line1Moved(self):
        self.lineMoved(1)

    def lineMoveFinished(self):
        self.sigRegionChangeFinished.emit(self)

    def mouseDragEvent(self, ev):
        if ev.button() != QtCore.Qt.MouseButton.LeftButton:
            return
        ev.accept()
        
        if ev.isStart():
            bdp = ev.buttonDownPos()
            self.cursorOffset = (self.lines[0].value()-bdp.x(), self.lines[1].value()-bdp.y())
            self.startPosition = self.get_value()
            self.moving = True
            
        if not self.moving:
            return
            
        self.lines[0].blockSignals(True)  # only want to update once
        cur_mouse_pos = ev.pos()
        for i, l in enumerate(self.lines):
            l.setPos(self.cursorOffset[i] + cur_mouse_pos[i])
        self.lines[0].blockSignals(False)
        self.prepareGeometryChange()
        
        if ev.isFinish():
            self.moving = False
            self.sigRegionChangeFinished.emit(self)
        else:
            self.sigChangedCurX.emit(self)
            self.sigChangedCurY.emit(self)
    
    def get_value(self):
        return (self.lines[0].value(), self.lines[1].value())
    
    def set_value(self, x, y):
        return (self.lines[0].setValue(x), self.lines[1].setValue(y))

    def mouseClickEvent(self, ev):
        if self.moving and ev.button() == QtCore.Qt.MouseButton.RightButton:
            ev.accept()
            for i, l in enumerate(self.lines):
                l.setPos(self.startPosition[i])
            self.moving = False
            self.sigRegionChanged.emit(self)
            self.sigRegionChangeFinished.emit(self)

    def hoverEvent(self, ev):
        if (not ev.isExit()) and ev.acceptDrags(QtCore.Qt.MouseButton.LeftButton):
            self.setMouseHover(True)
        else:
            self.setMouseHover(False)
            
    def setMouseHover(self, hover):
        ## Inform the item that the mouse is(not) hovering over it
        if self.mouseHovering == hover:
            return
        self.mouseHovering = hover
        if hover:
            self.currentBrush = self.hoverBrush
        else:
            self.currentBrush = self.brush
        self.update()
