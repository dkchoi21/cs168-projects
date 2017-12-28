"""
Your learning switch warm-up exercise for CS-168.

Start it up with a commandline like...

  ./simulator.py --default-switch-type=learning_switch topos.rand --links=0

"""

import sim.api as api
import sim.basics as basics


class LearningSwitch(api.Entity):
    """
    A learning switch.

    Looks at source addresses to learn where endpoints are.  When it doesn't
    know where the destination endpoint is, floods.

    This will surely have problems with topologies that have loops!  If only
    someone would invent a helpful poem for solving that problem...

    """

    def __init__(self):
        """
        Do some initialization.

        You probably want to do something in this method.

        """
        self.table = {}


    def handle_link_down(self, port):
        """
        Called when a port goes down (because a link is removed)

        You probably want to remove table entries which are no longer
        valid here.

        """
        copy_table = dict(self.table)
        for k in copy_table:
            tmp = self.table[k]
            if port in tmp:
                self.table[k].remove(port)
                if len(self.table[k]) == 0:
                    self.table.pop(k)


    def handle_rx(self, packet, in_port):
        """
        Called when a packet is received.

        You most certainly want to process packets here, learning where
        they're from, and either forwarding them toward the destination
        or flooding them.

        """

        #In handle_rx, you can see that you should be handling three types of packets:
        # HostDiscoveryPackets, RoutePackets, and normal data packets.
        # Your implementation needs to handle all types of these packets at the same time
        # and not wait for routing state to converge before being able to send data packets.

        # The source of the packet can obviously be reached via the input port, so
        # we should "learn" that the source host is out that port.  If we later see
        # a packet with that host as the *destination*, we know where to send it!
        # But it's up to you to implement that.  For now, we just implement a
        # simple hub.

        if isinstance(packet, basics.HostDiscoveryPacket):
            # Don't forward discovery messages
            src = packet.src
            self.table[src] = [in_port]
            return
        else:
            if packet.src not in self.table:
                self.table[packet.src] = [in_port]
            if packet.dst not in self.table:
                self.send(packet, in_port, flood=True)
            else:
                port = self.table[packet.dst]
                self.send(packet, port, flood=False)

