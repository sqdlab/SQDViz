import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import functions as fn
import numpy as np


# class Cursor_Cross(pg.GraphItem):
#     def __init__(self):
#         self.dragPoint = None
#         self.dragOffset = None
#         self.pos = np.array([0,0])
#         pg.GraphItem.__init__(self)
#         self.scatter.sigClicked.connect(self.clicked)
#         self.setData(pos=np.array([[0.0,0.0]]), size=1, symbol=['o'], pxMode=False)
#         self.line_h = pg.InfiniteLine(QtCore.QPointF(0.00, 0), angle=90)
#         self.updateGraph()
        
#     def setData(self, **kwds):
#         self.data = kwds
        
#     def updateGraph(self):
#         pg.GraphItem.setData(self, **self.data)
#         self.line_h.setValue(self.data['pos'][0][0])
        
#     def mouseDragEvent(self, ev):
#         if ev.button() != QtCore.Qt.LeftButton:
#             ev.ignore()
#             return
        
#         if ev.isStart():
#             # We are already one step into the drag.
#             # Find the point(s) at the mouse cursor when the button was first 
#             # pressed:
#             pos = ev.buttonDownPos()
#             pts = self.scatter.pointsAt(pos)
#             if len(pts) == 0:
#                 ev.ignore()
#                 return
#             self.dragPoint = pts[0]
#             self.dragOffset = self.data['pos'][0] - pos
#         elif ev.isFinish():
#             self.dragPoint = None
#             return
#         else:
#             if self.dragPoint is None:
#                 ev.ignore()
#                 return
#         self.data['pos'][0] = ev.pos() + self.dragOffset
#         self.updateGraph()
#         ev.accept()
        
#     def clicked(self, pts):
#         print("clicked: %s" % pts)


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
    Vertical = 0
    Horizontal = 1
    _orientation_axis = {
        Vertical: 0,
        Horizontal: 1,
        'vertical': 0,
        'horizontal': 1,
        }
    
    def __init__(self, value=1, brush=None, pen=None,
                 hoverBrush=None, hoverPen=None, movable=True, bounds=None, 
                 span=(0, 1), clipItem=None):        
        pg.GraphicsObject.__init__(self)
        self.blockLineSignal = False
        self.moving = False
        self.mouseHovering = False
        self.span = span
        self.clipItem = clipItem

        self._boundingRectCache = None
        self._clipItemBoundsCache = None
        
        # note LinearRegionItem.Horizontal and LinearRegionItem.Vertical
        # are kept for backward compatibility.
        lineKwds = dict(
            movable=movable,
            bounds=bounds,
            span=span,
            pen=pen,
            hoverPen=hoverPen,
        )
            
        # self.lines[0].setTransform(tr, True)
        self.lines = [pg.InfiniteLine(QtCore.QPointF(value, 0), angle=90, **lineKwds), pg.InfiniteLine(QtCore.QPointF(value, 0), angle=0, **lineKwds)]
        
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
        
        self.setMovable(movable)

    def getRegion(self):
        """Return the values at the edges of the region."""

        r = (self.lines[0].value(), self.lines[0].value())
        return r

    def setRegion(self, rgn):
        """Set the values for the edges of the region.
        
        ==============   ==============================================
        **Arguments:**
        rgn              A list or tuple of the lower and upper values.
        ==============   ==============================================
        """
        # if self.lines[0].value() == rgn[0] and self.lines[1].value() == rgn[1]:
        #     return
        # self.blockLineSignal = True
        self.lines[0].setValue(rgn[0])
        # self.blockLineSignal = False
        # self.lines[1].setValue(rgn[1])
        #self.blockLineSignal = False
        self.lineMoved(0)
        # self.lineMoved(1)
        self.lineMoveFinished()

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

    def setBounds(self, bounds):
        """Set ``(min, max)`` bounding values for the region.

        The current position is only affected it is outside the new bounds. See
        :func:`~pyqtgraph.LinearRegionItem.setRegion` to set the position of the region.

        Use ``(None, None)`` to disable bounds.
        """
        if self.clipItem is not None:
            self.setClipItem(None)
        self._setBounds(bounds)

    def _setBounds(self, bounds):
        # internal impl so user-facing setBounds can clear clipItem and clipItem can
        # set bounds without clearing itself
        for line in self.lines:
            line.setBounds(bounds)

    def setMovable(self, m=True):
        """Set lines to be movable by the user, or not. If lines are movable, they will 
        also accept HoverEvents."""
        for line in self.lines:
            line.setMovable(m)
        self.movable = m
        self.setAcceptHoverEvents(m)

    def setSpan(self, mn, mx):
        if self.span == (mn, mx):
            return
        self.span = (mn, mx)
        for line in self.lines:
            line.setSpan(mn, mx)
        self.update()

    def setClipItem(self, item=None):
        """Set an item to which the region is bounded.

        If ``None``, bounds are disabled.
        """
        self.clipItem = item
        self._clipItemBoundsCache = None
        if item is None:
            self._setBounds((None, None))
        if item is not None:
            self._updateClipItemBounds()

    def _updateClipItemBounds(self):
        # set region bounds corresponding to clipItem
        item_vb = self.clipItem.getViewBox()
        if item_vb is None:
            return

        item_bounds = item_vb.childrenBounds(items=(self.clipItem,))
        if item_bounds == self._clipItemBoundsCache or None in item_bounds:
            return

        self._clipItemBoundsCache = item_bounds

        if self.orientation in ('horizontal', pg.LinearRegionItem.Horizontal):
            self._setBounds(item_bounds[1])
        else:
            self._setBounds(item_bounds[0])

    def boundingRect(self):
        br = QtCore.QRectF(self.viewRect())  # bounds of containing ViewBox mapped to local coords.

        if self.clipItem is not None:
            self._updateClipItemBounds()

        rng = self.getRegion()
        br.setTop(rng[0])
        br.setBottom(rng[1])
        length = br.width()
        br.setRight(br.left() + length * self.span[1])
        br.setLeft(br.left() + length * self.span[0])

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
        if not self.movable or ev.button() != QtCore.Qt.MouseButton.LeftButton:
            return
        ev.accept()
        
        if ev.isStart():
            bdp = ev.buttonDownPos()
            self.cursorOffsets = [l.pos() - bdp for l in self.lines]
            self.startPositions = [l.pos() for l in self.lines]
            self.moving = True
            
        if not self.moving:
            return
            
        self.lines[0].blockSignals(True)  # only want to update once
        for i, l in enumerate(self.lines):
            l.setPos(self.cursorOffsets[i] + ev.pos())
        self.lines[0].blockSignals(False)
        self.prepareGeometryChange()
        
        if ev.isFinish():
            self.moving = False
            self.sigRegionChangeFinished.emit(self)
        else:
            self.sigRegionChanged.emit(self)
    
    def get_value(self):
        return (self.lines[0].value(), self.lines[1].value())

    def mouseClickEvent(self, ev):
        if self.moving and ev.button() == QtCore.Qt.MouseButton.RightButton:
            ev.accept()
            for i, l in enumerate(self.lines):
                l.setPos(self.startPositions[i])
            self.moving = False
            self.sigRegionChanged.emit(self)
            self.sigRegionChangeFinished.emit(self)

    def hoverEvent(self, ev):
        if self.movable and (not ev.isExit()) and ev.acceptDrags(QtCore.Qt.MouseButton.LeftButton):
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

