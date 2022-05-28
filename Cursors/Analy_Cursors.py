import sys, inspect
import pyqtgraph as pg
from PySide6 import QtGui

class Analy_Cursor:
    def __init__(self, name, colour, ext_callback):
        self._name = name
        self._visible = False
        self._is_drag = False   #Set this to whatever one wants during a drag and 'None' if not in a drag...
        self._drag_threshold = 10
        self.has_changed = False
        self._colour = colour
        self._ext_callback = ext_callback

    @property
    def Name(self):
        return self._name
    @Name.setter
    def Name(self, new_name):
        self._name = new_name

    @property
    def Colour(self):
        return self._colour

    @property
    def Visible(self):
        return self._visible
    @Visible.setter
    def Visible(self, bool_val):
        self._visible = bool_val
        self._set_visibility(bool_val)
    
    def _set_visibility(self, bool_val):
        raise NotImplementedError()

    def init_cursor(self, plot_widget):
        raise NotImplementedError()
    
    def release_from_plots(self):
        raise NotImplementedError()

    @staticmethod
    def get_all_analysis_cursors():
        is_class_member = lambda member: inspect.isclass(member) and member.__module__ == __name__
        clsmembers = inspect.getmembers(sys.modules[__name__], is_class_member)
        #Returns a dictionary of function name and a post-processor object to boot!
        return { x[1].Type:x[1] for x in clsmembers if x[0].startswith('AC_') }

class AC_RegionX(Analy_Cursor):
    Type = 'X-Region'
    Prefix = 'X'
    
    def __init__(self, name, colour, ext_callback):
        super().__init__(name, colour, ext_callback)
        self.region = None
        self.plot_widget = None
    
    @property
    def Summary(self):
        return f'[{self.x1},{self.x2}]'

    @property
    def x1(self):
        if self.region:
            min_x, max_x = self.region.getRegion()
            return min_x
        else:
            return 0

    @property
    def x2(self):
        if self.region:
            min_x, max_x = self.region.getRegion()
            return max_x
        else:
            return 0

    def init_cursor(self, plot_widget):
        penBase = pg.mkPen(self.Colour)
        h,s,v = penBase.color().hue(), penBase.color().saturation(), penBase.color().value()
        invcol = QtGui.QColor.fromHsvF(((h + 128) % 255)/255.0, s/255.0, v/255.0)
        penHover = pg.mkPen(invcol)
        #
        brushBase = QtGui.QBrush(QtGui.QColor(penBase.color().red(), penBase.color().green(), penBase.color().blue(), 50))
        invcol.setAlpha(100)
        brushInv = QtGui.QBrush(invcol)
        #
        lineKwds = dict(movable=True, pen=penBase, hoverPen=penHover, brush=brushBase, hoverBrush=brushInv)
        #
        self.region = pg.LinearRegionItem(**lineKwds)
        self.plot_widget = plot_widget
        self.plot_widget.addItem(self.region, ignoreBounds=True)
        self._set_visibility(self.Visible)
        self.region.sigRegionChanged.connect(self._event_region_changed)
    
    def _event_region_changed(self):
        self._ext_callback(self)

    def release_from_plots(self):
        try: self.region.sigRegionChanged.disconnect(self._event_region_changed) 
        except Exception: pass
        if self.plot_widget:
            self.plot_widget.removeItem(self.region)
            self.plot_widget = None
        del self.region
        self.region = None

    def _set_visibility(self, bool_val):
        if self.region:
            self.region.setVisible(bool_val)

class AC_RegionY(Analy_Cursor):
    Type = 'Y-Region'
    Prefix = 'Y'
    
    def __init__(self, name, colour, ext_callback):
        super().__init__(name, colour, ext_callback)
        self.region = None
        self.plot_widget = None
    
    @property
    def Summary(self):
        return f'[{self.y1},{self.y2}]'

    @property
    def y1(self):
        if self.region:
            min_y, max_y = self.region.getRegion()
            return min_y
        else:
            return 0

    @property
    def y2(self):
        if self.region:
            min_y, max_y = self.region.getRegion()
            return max_y
        else:
            return 0

    def init_cursor(self, plot_widget):
        penBase = pg.mkPen(self.Colour)
        h,s,v = penBase.color().hue(), penBase.color().saturation(), penBase.color().value()
        invcol = QtGui.QColor.fromHsvF(((h + 128) % 255)/255.0, s/255.0, v/255.0)
        penHover = pg.mkPen(invcol)
        #
        brushBase = QtGui.QBrush(QtGui.QColor(penBase.color().red(), penBase.color().green(), penBase.color().blue(), 50))
        invcol.setAlpha(100)
        brushInv = QtGui.QBrush(invcol)
        #
        lineKwds = dict(movable=True, pen=penBase, hoverPen=penHover, brush=brushBase, hoverBrush=brushInv)
        #
        self.region = pg.LinearRegionItem(orientation='horizontal', **lineKwds)
        self.plot_widget = plot_widget
        self.plot_widget.addItem(self.region, ignoreBounds=True)
        self._set_visibility(self.Visible)
        self.region.sigRegionChanged.connect(self._event_region_changed)
    
    def _event_region_changed(self):
        self._ext_callback(self)

    def release_from_plots(self):
        try: self.region.sigRegionChanged.disconnect(self._event_region_changed) 
        except Exception: pass
        if self.plot_widget:
            self.plot_widget.removeItem(self.region)
            self.plot_widget = None
        del self.region
        self.region = None

    def _set_visibility(self, bool_val):
        if self.region:
            self.region.setVisible(bool_val)
