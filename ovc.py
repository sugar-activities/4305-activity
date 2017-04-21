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
:mod: `OpenVideoChat/OpenVideoChat.activity/ovc` -- Open Video Chat
=======================================================================

.. moduleauthor:: Justin Lewis <jlew.blackout@gmail.com>
.. moduleauthor:: Taylor Rose <tjr1351@rit.edu>
.. moduleauthor:: Fran Rogers <fran@dumetella.net>
.. moduleauthor:: Remy DeCausemaker <remyd@civx.us>
.. moduleauthor:: Luke Macken <lmacken@redhat.com>
"""

from gettext import gettext as _

from sugar.activity.activity import Activity, ActivityToolbox
import gtk
import gst
import gobject

from sugar.graphics.alert import NotifyAlert, Alert

from gui import Gui
from sugar_network_stack import SugarNetworkStack
from gst_stack import GSTStack
from sugar import profile

class OpenVideoChatActivity(Activity):
    def __init__(self, handle):
        Activity.__init__(self, handle)

        # gobject is used for timeing (will be removed when rtp is implemented)
        gobject.threads_init()

        # Set if they started the activity
        self.isServer = not self._shared_activity

        # Let sugar know we only want a 1 to 1 share (limit to 2 people)
        # Note this is not enforced by sugar yet :(
        self.max_participants = 2

        #FIXME: This is a hack to only allow our ip to be sent once.
        #AKA disables others from double streaming
        if self.isServer:
            # server will send out ip twice, first when joinning empty channel
            # second when the user joins
            self.sent_ip = 2
        else:
            self.sent_ip = 1

        # INITIALIZE GUI
        ################
        self.set_title('OpenVideoChat')

        # Setup Gui
        ###########
        self.gui = Gui(self)
        self.gui.show()
        self.set_canvas(self.gui)

        # Setup Network Stack
        #####################
        self.netstack = SugarNetworkStack(self)
        self._sh_hnd = self.connect('shared', self.netstack.shared_cb)
        self._jo_hnd = self.connect('joined', self.netstack.joined_cb)

        # Setup Pipeline
        #################
        self.gststack = GSTStack( self.gui.send_video_to_screen )
        self.gststack.build_incoming_pipeline()
        gobject.idle_add( self.gststack.start_stop_incoming_pipeline, True )
        
        print "Activity Started"
        
    def can_close( self ):
        print "Closing, stopping pipelines"
        self.gststack.start_stop_incoming_pipeline(False)
        self.gststack.start_stop_outgoing_pipeline(False)
        return True

    def _alert(self, title, text=None, timeout=5):
        alert = NotifyAlert(timeout=timeout)
        alert.props.title = title
        alert.props.msg = text
        self.add_alert(alert)
        alert.connect('response', self._alert_cancel_cb)
        alert.show()

    def _alert_cancel_cb(self, alert, response_id):
        self.remove_alert(alert)

    def net_cb(self, src, args):
        """
        Callback for network commands
        """
        if src == "chat":
            message, sender = args
            self.gui.add_chat_text( message )

        elif src == "join":
            handle = self.netstack.get_tube_handle()
            if handle and self.sent_ip > 0:
                import socket
                import fcntl
                import struct
                import array
                # http://code.activestate.com/recipes/439094-get-the-ip-address-associated-with-a-network-inter/
                def get_ip_address(ifname):
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    return socket.inet_ntoa(fcntl.ioctl(
                        s.fileno(),
                        0x8915,  # SIOCGIFADDR
                        struct.pack('256s', ifname[:15])
                    )[20:24])

                #http://code.activestate.com/recipes/439093-get-names-of-all-up-network-interfaces-linux-only/
                def all_interfaces():
                    max_possible = 128  # arbitrary. raise if needed.
                    bytes = max_possible * 32
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    names = array.array('B', '\0' * bytes)
                    outbytes = struct.unpack('iL', fcntl.ioctl(
                        s.fileno(),
                        0x8912,  # SIOCGIFCONF
                        struct.pack('iL', bytes, names.buffer_info()[0])
                    ))[0]
                    namestr = names.tostring()
                    return [namestr[i:i+32].split('\0', 1)[0] for i in range(0, outbytes, 32)]


                for interface in all_interfaces():
                    if interface != 'lo':
                        try:
                            ip = get_ip_address(interface)
                            self.sent_ip = self.sent_ip - 1
                            handle.announce_ip(ip)
                            break
                        except:
                            print "Interface %s did not give ip" % interface
                else:
                    print "Could not find ip address"
                    
        elif src == "ip":
            #FIXME: Store ip with user so we can make user lists to switch between later on
            if not hasattr( self, 'out' ):
                    #~ s1,s2,s3 = self.out.get_state()
                    #~ if s2 == gst.STATE_PLAYING:
                        #~ print args,"has sent its ip, ignoring as we are allready streaming"
                    #~ else:

                self.gststack.build_outgoing_pipeline( args )

                # FIXME
                gobject.timeout_add(5000, self.gststack.start_stop_outgoing_pipeline)
                
            else:
                print args,"has sent its ip, ignoring as we are allready streaming"

        elif src == "buddy_add":
            self.gui.add_chat_text(_("%s has joined the chat") % args)

        elif src == "buddy_rem":
            self.gui.add_chat_text(_("%s has left the chat") % args)

    def send_chat_text(self, text):
        handle = self.netstack.get_tube_handle()
        prof = profile.get_nick_name()

        if handle:
            handle.send_chat_text( "<%s> %s" % (prof, text) )
            
    #
    # Save Chat Log
    #
    
    def write_file(self, file_path):
        file = open(file_path, 'w')
        file.write( self.gui.get_history() )
        file.close()
        
    #
    # Load Chat Log
    #
    
    def read_file(self, file_path):
        file = open(file_path, 'r')
        
        self.gui.add_chat_text(file.read())
            
        file.close()
