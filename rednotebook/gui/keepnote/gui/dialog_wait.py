"""

    KeepNote
    General Wait Dialog

"""

# python imports
import os, sys, threading, time, traceback


# pygtk imports
import pygtk
pygtk.require('2.0')
import gtk.glade
import gobject

# keepnote imports
import keepnote
from keepnote import get_resource
from keepnote import tasklib    
    

class WaitDialog (object):
    """General dialog for background tasks"""
    
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self._task = None

    
    def show(self, title, message, task, cancel=True):
        self.xml = gtk.glade.XML(get_resource("rc", "keepnote.glade"),
                                 "wait_dialog")
        self.dialog = self.xml.get_widget("wait_dialog")
        self.xml.signal_autoconnect(self)
        self.dialog.connect("close", self._on_close)
        self.dialog.set_transient_for(self.parent_window)
        self.text = self.xml.get_widget("wait_text_label")
        self.progressbar = self.xml.get_widget("wait_progressbar")

        self.dialog.set_title(title)
        self.text.set_text(message)
        self._task = task
        self._task.run()

        cancel_button = self.xml.get_widget("cancel_button")
        cancel_button.set_sensitive(cancel)

        self.dialog.show()
        proc = threading.Thread(target=self._on_idle)
        proc.start()
        self.dialog.run()
        self._task.join()


    def _on_idle(self):
        """Idle thread"""
        
        while not self._task.is_stopped():
            def gui_update():
                gtk.gdk.threads_enter()
                percent = self._task.get_percent()
                if percent is None:            
                    self.progressbar.pulse()
                else:
                    self.progressbar.set_fraction(percent)

                # filter for messages we process
                messages = filter(lambda x: isinstance(x, tuple) and len(x) == 2,
                                  self._task.get_messages())
                texts = filter(lambda (a,b): a == "text", messages)
                details = filter(lambda (a,b): a == "detail", messages)

                if len(texts) > 0:
                    self.text.set_text(texts[-1][1])
                if len(details) > 0:
                    self.progressbar.set_text(details[-1][1])
                
                gtk.gdk.threads_leave()
            gobject.idle_add(gui_update)
            
            time.sleep(.1)
        
        # kill dialog and stop idling
        gobject.idle_add(lambda: self.dialog.destroy())
        


    def _on_task_update(self):
        pass


    def _on_close(self, window):
        pass

    def on_cancel_button_clicked(self, button):
        """Attempt to stop the task"""

        self.text.set_text("Canceling...")
        self._task.stop()

        
