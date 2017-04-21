#    This file is part of OpenVideoChat.
#
#    OpenVideoChat is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    OpenVideoChat is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with OpenVideoChat.  If not, see <http://www.gnu.org/licenses/>.
"""
:mod: `OpenVideoChat/OpenVideoChat.activity/gui` -- Open Video Chat Gui
=======================================================================

.. moduleauthor:: Justin Lewis <jlew.blackout@gmail.com>
.. moduleauthor:: Taylor Rose <tjr1351@rit.edu>
.. moduleauthor:: Fran Rogers <fran@dumetella.net>
.. moduleauthro:: Remy DeCausemaker <remyd@civx.us>
"""

import gtk
from gettext import gettext as _

from sugar.activity.activity import ActivityToolbox
from sugar.graphics.toolbutton import ToolButton

class Gui( gtk.VBox ):
    def __init__(self, activity):
        gtk.VBox.__init__(self)

        self.activity = activity

        mov_box = gtk.HBox()
        
        # Add movie window
        self.movie_window = gtk.DrawingArea()
        self.movie_window_preview = gtk.DrawingArea()
        mov_box.pack_start( self.movie_window )
        mov_box.pack_start( self.movie_window_preview )

        self.pack_start( mov_box )
        # Add Chat section
        ##################

        # Chat expander allows chat to be hidden/shown
        chat_expander = gtk.Expander(_("Chat"))
        chat_expander.set_expanded( True )
        self.pack_start( chat_expander, False )

        chat_holder = gtk.VBox()
        chat_expander.add(chat_holder)

        # Create entry and history view for chat
        chat_history = gtk.ScrolledWindow()
        chat_history.set_policy( gtk.POLICY_NEVER,gtk.POLICY_AUTOMATIC )
        
        self.chat_text = gtk.TextBuffer()
        self.text_view = gtk.TextView( self.chat_text )
        self.text_view.set_editable( False )
        self.text_view.set_size_request( -1, 200 )
        
        chat_history.add( self.text_view )
        
        # Send button to complete feel of a chat program
        self.chat_entry = gtk.Entry()
        self.chat_entry.connect("activate",self.send_chat)
        send_but = gtk.Button( _("Send") )
        send_but.connect("clicked", self.send_chat)

        # Wrap button and entry in hbox so they are on the same line
        chat_entry_hbox = gtk.HBox()
        chat_entry_hbox.pack_start( self.chat_entry )
        chat_entry_hbox.pack_end( send_but, False )

        # Add chat history and entry to expander
        chat_holder.pack_start( chat_history )
        chat_holder.pack_start( chat_entry_hbox, False )

        # Show gui
        self.build_toolbars()
        self.show_all()
        
        #scroll to bottom
        self.text_view.scroll_to_iter( self.chat_text.get_end_iter(), 0.1 )
        
    def get_history(self):
        return self.chat_text.get_text( self.chat_text.get_start_iter(), self.chat_text.get_end_iter() )

    def add_chat_text(self, text):
        self.chat_text.insert( self.chat_text.get_end_iter(), "%s\n" % text )
        self.text_view.scroll_to_iter( self.chat_text.get_end_iter(), 0.1 )
        
    def send_chat(self, w):
        if self.chat_entry.get_text != "":
            self.activity.send_chat_text( self.chat_entry.get_text() )
            self.chat_entry.set_text("")

    def build_toolbars(self):
        self.settings_bar = gtk.Toolbar()

        self.settings_buttons = {}

        self.settings_buttons['reload_video'] = ToolButton('view-spiral')
        self.settings_buttons['reload_video'].set_tooltip(_("Reload Screen"))
        self.settings_buttons['reload_video'].connect("clicked", self.force_redraw, None)
        self.settings_bar.insert(self.settings_buttons['reload_video'], -1)

        self.toolbox = ActivityToolbox(self.activity)
        self.toolbox.add_toolbar(_("Settings"), self.settings_bar)

        self.activity.set_toolbox(self.toolbox)
        self.toolbox.show_all()

    def force_redraw(self, widget, value=None):
        # Fixme: This should not be required, this is a hack for now until
        # a better solution that works is found
        self.movie_window.hide()
        self.movie_window_preview.hide()
        self.movie_window.show()
        self.movie_window_preview.show()

    def send_video_to_screen(self, source, screen):
        if screen == 'MAIN':
            source.set_xwindow_id(self.movie_window.window.xid)
        elif screen == 'PREVIEW':
            source.set_xwindow_id(self.movie_window_preview.window.xid)
        
