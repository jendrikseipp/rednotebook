import wx

class redNotebookConfig(wx.FileConfig):
    def __init__(self, *args, **kargs):
        wx.FileConfig.__init__(self, *args, **kargs)
        

