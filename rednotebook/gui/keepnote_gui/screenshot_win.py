
import sys, os

# win32api imports
try:
    import win32api
    import win32gui
    import win32con
    import win32ui
except ImportError:
    pass

_g_class_num = 0
 

def capture_screen(filename, x, y, x2, y2):
    """Captures a screenshot from a region of the screen"""

    if x > x2:
        x, x2 = x2, x
    if y > y2:
        y, y2 = y2, y
    w, h = x2 - x, y2 - y
    
    screen_handle = win32gui.GetDC(0)
    
    screen_dc = win32ui.CreateDCFromHandle(screen_handle)
    shot_dc = screen_dc.CreateCompatibleDC()
    
    print 

    shot_bitmap = win32ui.CreateBitmap()
    shot_bitmap.CreateCompatibleBitmap(screen_dc, w, h)

    shot_dc.SelectObject(shot_bitmap)
    shot_dc.BitBlt((0, 0), (w, h), screen_dc, (x, y), win32con.SRCCOPY)

    shot_bitmap.SaveBitmapFile(shot_dc, filename)

   
class Window (object):
    """Class for basic MS Windows window"""

    def __init__(self, title="Untitled",
                 style=None, 
                 exstyle=None,
                 pos=(0, 0),
                 size=(400, 400),
                 background=None,
                 message_map = {},
                 cursor=None):
        global _g_class_num

        if style is None:
            style = win32con.WS_OVERLAPPEDWINDOW
        if exstyle is None:
            style = win32con.WS_EX_LEFT
        if background is None:
            background = win32con.COLOR_WINDOW
        if cursor is None:
            cursor = win32con.IDC_ARROW

        
        self._instance = win32api.GetModuleHandle(None)
        
        self.message_map = {win32con.WM_DESTROY: self._on_destroy}
        self.message_map.update(message_map)
        
        _g_class_num += 1
        class_name = "class_name%d" % _g_class_num
        wc = win32gui.WNDCLASS()
        wc.hInstance = self._instance
        wc.lpfnWndProc = self.message_map # could also specify a wndproc
        wc.lpszClassName = class_name
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wc.hbrBackground = background
        wc.cbWndExtra = 0
        wc.hCursor = win32gui.LoadCursor(0, cursor)
        wc.hIcon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
       
        class_atom = win32gui.RegisterClass(wc)
        
        # C code: wc.cbWndExtra = DLGWINDOWEXTRA + sizeof(HBRUSH) + (sizeof(COLORREF));
        #wc.cbWndExtra = win32con.DLGWINDOWEXTRA + struct.calcsize("Pi")
        #wc.hIconSm = 0

        self._handle = win32gui.CreateWindowEx(exstyle,
                                   class_atom, title,
                                   style, #win32con.WS_POPUP, # | win32con.WS_EX_TRANSPARENT,
                                   pos[0], pos[1], size[0], size[1],
                                   0, # no parent
                                   0, # no menu
                                   self._instance,
                                   None)
        
    def show(self, enabled=True):
        if enabled:
            win32gui.ShowWindow(self._handle, win32con.SW_SHOW)
        else:
            win32gui.ShowWindow(self._handle, win32con.SW_HIDE)

    def maximize(self):
        win32gui.ShowWindow(self._handle, win32con.SW_SHOWMAXIMIZED)
    
    def activate(self):
        win32gui.SetForegroundWindow(self._handle) #SwitchToThisWindow(self._handle, False)
    
    def _on_destroy(self, hwnd, message, wparam, lparam):
        self.close()
        return True
    
    def close(self):
        #win32gui.PostQuitMessage(0)
        win32gui.DestroyWindow(self._handle)


        
class WinLoop (object):
    def __init__(self):
        self._running = True
    
    def start(self):
        while self._running:
            b, msg = win32gui.GetMessage(0, 0, 0)
            if not msg:
                break
            win32gui.TranslateMessage(msg)
            win32gui.DispatchMessage(msg)
    
    def stop(self):
        self._running = False

        
class ScreenShotWindow (Window):
    """ScreenShot Window"""

    def __init__(self, filename, shot_callback=None):
        x, y, w, h = win32gui.GetWindowRect(win32gui.GetDesktopWindow())
        
        Window.__init__(self, 
            "Screenshot", pos=(x,y), size=(w,h),
            style = win32con.WS_POPUP,
            exstyle = win32con.WS_EX_TRANSPARENT,
            background = 0,
            message_map = { 
                win32con.WM_MOUSEMOVE: self._on_mouse_move,
                win32con.WM_LBUTTONDOWN: self._on_mouse_down,
                win32con.WM_LBUTTONUP: self._on_mouse_up
            },
            cursor=win32con.IDC_CROSS)
        
        self._filename = filename
        self._shot_callback = shot_callback
        self._drag = False
        self._draw = False
    
    def _on_mouse_down(self, hwnd, message, wparam, lparam):
        """Mouse down event"""
        self._drag = True
        self._start = win32api.GetCursorPos()
    
    def _on_mouse_up(self, hwnd, message, wparam, lparam):
        """Mouse up event"""
        
        if self._draw:
            # cleanup rectangle on desktop
            self._drag = False
            self._draw = False
            
            hdc = win32gui.CreateDC("DISPLAY", None, None)
            pycdc = win32ui.CreateDCFromHandle(hdc)
            pycdc.SetROP2(win32con.R2_NOTXORPEN)
            
            win32gui.Rectangle(hdc, self._start[0], self._start[1],
                                    self._end[0], self._end[1])
            
            # save bitmap
            capture_screen(self._filename, self._start[0], self._start[1],
                           self._end[0], self._end[1])
    
        self.close()
        
        if self._shot_callback:
            self._shot_callback()
            
    
    def _on_mouse_move(self, hwnd, message, wparam, lparam):
        """Mouse moving event"""
        
        # get current mouse coordinates
        x, y = win32api.GetCursorPos()
        
        if self._drag:
            
            hdc = win32gui.CreateDC("DISPLAY", None, None)
            pycdc = win32ui.CreateDCFromHandle(hdc)
            pycdc.SetROP2(win32con.R2_NOTXORPEN)
            
            # erase old rectangle
            if self._draw:
                win32gui.Rectangle(hdc, self._start[0], self._start[1],
                                   self._end[0], self._end[1])
            
            # draw new rectangle
            self._draw = True
            win32gui.Rectangle(hdc, self._start[0], self._start[1],
                                    x, y)
            self._end = (x, y)
            
            #DeleteDC ( hdc);

def take_screenshot(filename):
    win32gui.InitCommonControls()

    def click():
        loop.stop()
    
    loop = WinLoop()
    win = ScreenShotWindow(filename, click)
    win.maximize()
    win.activate()
    loop.start()
    
    #win32gui.PumpMessages()
            

            
            

def main(argv):

    if len(argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "screenshot.bmp"

    take_screenshot(filename)

if __name__ == "__main__":
    main(sys.argv)
    
    





