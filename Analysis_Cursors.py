
class Analysis_Cursor:
    def __init__(self, name):
        self._name = name
        self._visible = False

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

class AC_Xregion(Analysis_Cursor):
    def __init__(self, name):
        super().__init__(name)
        self.x1 = 0
        self.x2 = 0

    @property
    def Type(self):
        return 'X-Region'
    @property
    def Prefix(self):
        return 'X'
    @property
    def Summary(self):
        return f'[{self.x1,self.x2}]'
