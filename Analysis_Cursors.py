from matplotlib.patches import Rectangle
from matplotlib.backend_bases import (key_press_handler, MouseButton)

class Analysis_Cursor:
    def __init__(self, name):
        self._name = name
        self._visible = False
        self._is_drag = False   #Set this to whatever one wants during a drag and 'None' if not in a drag...
        self._drag_threshold = 10
        self.has_changed = False

    @property
    def Name(self):
        return self._name
    @Name.setter
    def Name(self, new_name):
        self._name = new_name

    @property
    def Visible(self):
        return self._visible
    @Visible.setter
    def Visible(self, bool_val):
        self._visible = bool_val

    @property
    def Dragging(self):
        return self._is_drag == 'None'

    def prepare_plot(self, pltfrm, ax):
        #NOTE: MUST CALL THIS IN SUPER FIRST!
        self.ax = ax
        self.pltfrm = pltfrm
        self.pltfrm.Canvas.mpl_connect('motion_notify_event', self._move_cursor)
        self.pltfrm.Canvas.mpl_connect('button_release_event', self.event_mouse_released)

    def event_drag(self, coord):
        '''
        Handles the drag event by noting the current mouse coordinate that is being dragged. The presumption is that
        the left-mouse button is being held down and that the current cursor is being dragged.

        Input:
            - coord - Current coordinate (x,y) of the mouse (in plotting coordinates) given as a tuple.
        '''
        raise NotImplementedError()

    def event_mouse_released(self, event):
        self._is_drag = 'None'

    def _event_mouse_pressed(self, mouse_coord):
        '''
        Handles whether or not to enter a drag phase on the cursor given that the mouse has been clicked over a particular plotting coordinate.

        Input:
            - mouse_coord - Current coordinate (x,y) of the mouse (in plotting coordinates) given as a tuple.
        '''
        raise NotImplementedError()

    def event_mouse_pressed(self, event):
        if event.inaxes and event.button == MouseButton.LEFT:
            self._event_mouse_pressed((event.xdata, event.ydata))

    def _move_cursor(self, event):
        if event.inaxes and event.button == MouseButton.LEFT:
            if self.Dragging != 'None':
                self.event_drag((event.xdata, event.ydata))
                #It is a motion-notify event - so the mouse has indeed moved into a new position...
                self.has_changed = True
        else:
            #Give up drag if mouse goes out of the axis...
            self._is_drag = 'None'

    def _pixel_distance(self, plotCoord1, plotCoord2):
        '''
        Returns the pixel distance between two coordinates on the plot. Useful when gauging whether the mouse is near a point on the plot.

        Inputs:
            - plotCoord1, plotCoord2 - Plot coordinates each given as a tuple (x,y)
        '''
        cur_ax_size = self.pltfrm.get_axis_size_px()
        xlimts = self.ax.get_xlim()
        ylimts = self.ax.get_ylim()
        plotCoord1_x = (plotCoord1[0]-xlimts[0])/(xlimts[1]-xlimts[0])*cur_ax_size[0]
        plotCoord1_y = (plotCoord1[1]-ylimts[0])/(ylimts[1]-ylimts[0])*cur_ax_size[1]
        plotCoord2_x = (plotCoord2[0]-xlimts[0])/(xlimts[1]-xlimts[0])*cur_ax_size[0]
        plotCoord2_y = (plotCoord2[1]-ylimts[0])/(ylimts[1]-ylimts[0])*cur_ax_size[1]

        return (abs(plotCoord1_x-plotCoord2_x), abs(plotCoord1_y-plotCoord2_y))

    def delete_from_plot(self):
        raise NotImplementedError()

    def render_blit(self):
        raise NotImplementedError()

class AC_Xregion(Analysis_Cursor):
    def __init__(self, name):
        super().__init__(name)
        self.x1 = 0
        self.x2 = 0.1

    @property
    def Type(self):
        return 'X-Region'
    @property
    def Prefix(self):
        return 'X'
    @property
    def Summary(self):
        return f'[{self.x1,self.x2}]'

    def prepare_plot(self, pltfrm, ax):
        super().prepare_plot(pltfrm, ax)
        self.rect = Rectangle((self.x1,0.0), 0.1, 0.1, angle=0.0, edgecolor='black', fill=False)
        self.ax.add_patch(self.rect)

    def delete_from_plot(self):
        if self.rect:
            self.rect.remove()

    def render_blit(self):
        if self.ax:
            lims = self.pltfrm.get_data_limits()
            self.rect.set_xy((self.x1, lims[2]))
            self.rect.set_width(self.x2-self.x1)
            self.rect.set_height(lims[3]-lims[2])
            self.ax.draw_artist(self.rect)

    def event_drag(self, coord):
        if self._is_drag == 'x1':
            self.x1 = coord[0]
        elif self._is_drag == 'x2':
            self.x2 = coord[0]
        
    def _event_mouse_pressed(self, mouse_coord):
        if self._pixel_distance(mouse_coord, (self.x1, mouse_coord[1]))[0] < self._drag_threshold:
            self._is_drag = 'x1'
        elif self._pixel_distance(mouse_coord, (self.x2, mouse_coord[1]))[0] < self._drag_threshold:
            self._is_drag = 'x2'
        else:
            self._is_drag = 'None'
