"""Your awesome Distance Vector router for CS 168."""
import math

import sim.api as api
import sim.basics as basics

# We define infinity as a distance of 16.
INFINITY = 16

class DVRouter(basics.DVRouterBase):
    # NO_LOG = True # Set to True on an instance to disable its logging
    # POISON_MODE = True # Can override POISON_MODE here
    # DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing

    def __init__(self):
        """
        Called when the instance is initialized.

        You probably want to do some additional initialization here.

        """

        self.start_timer()  # Starts calling handle_timer() at correct rate

        #ports : latency
        self.neighbor_ports = {}

        #dst : { port : [ latency, expiration] }
        self.dv_table = {}

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.

        The port attached to the link and the link latency are passed
        in.

        """

        self.neighbor_ports[port] = latency
        for destination in self.dv_table:
            dict_ports = self.dv_table[destination]
            rt_port, lat = self.get_shortest_route(dict_ports)
            route_packet = basics.RoutePacket(destination, lat)
            self.send(route_packet, port)

        #just send all my entire table to new neighbor

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.

        The port number used by the link is passed in.

        """
        # for all case you want to remove from the table  dv table and port table
        self.neighbor_ports.pop(port)
        copy_table = dict(self.dv_table)
        for dst in copy_table:
            if port in self.dv_table[dst]:
                self.dv_table[dst].pop(port)
                key_port, cost = self.get_shortest_route(self.dv_table[dst])
                # if key_port is None:
                if len(self.dv_table[dst]) == 0:
                    self.dv_table.pop(dst)
                    if self.POISON_MODE:
                        route_packet = basics.RoutePacket(dst, INFINITY)
                        self.send(route_packet, flood=True)

        #update my neighbors that i don't have access to this host

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.

        packet is a Packet (or subclass).
        port is the port number it arrived on.

        You definitely want to fill this in.

        """
        #self.log("RX %s on %s (%s)", packet, port, api.current_time())
        if isinstance(packet, basics.RoutePacket):
            dest = packet.destination
            lat = packet.latency
            lat_from_port = self.neighbor_ports[port]


            # if lat == INFINITY:
            #     self.dv_table.pop(dest)
            #     return
            # else:
            recalc_lat = lat + lat_from_port
            if lat == INFINITY:
                recalc_lat = INFINITY
            lst = [recalc_lat, self.ROUTE_TIMEOUT]
            if dest not in self.dv_table:
                self.dv_table[dest] = {port: lst}
            else:
                self.dv_table[dest][port] = lst


        elif isinstance(packet, basics.HostDiscoveryPacket):
            # dst of h1 : {port 0 : [latency, exp], port 1 : [latency, exp]}
            src = packet.src
            latency_to_host = self.neighbor_ports[port]

            tmp = {port: [latency_to_host, None]}
            if src in self.dv_table:
                self.dv_table[src][port] = [latency_to_host, None]
            else:
                self.dv_table[src] = tmp

        else:
            # Totally wrong behavior for the sake of demonstration only: send
            # the packet back to where it came from!

            if packet.src == packet.dst:
                return

            if packet.dst not in self.dv_table:
                return

            dict_ports = self.dv_table[packet.dst]
            rt_port, lat = self.get_shortest_route(dict_ports)
            if lat == INFINITY:
                self.log("Too Infinity and Beyond")
                return
            self.send(packet, rt_port)



    def handle_timer(self):
        """
        Called periodically.

        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.

        """
        #every 5 seconds the route sends out Route Packets

        self.decrement_expiration_time()

        for destination in self.dv_table:
            dict_ports = self.dv_table[destination]
            rt_port, lat = self.get_shortest_route(dict_ports)
            route_packet = basics.RoutePacket(destination, lat)
            self.send(route_packet, rt_port, flood=True)

    #route is identified by its port and dst
    def get_shortest_route(self, dict_ports):
        min_cost = INFINITY
        key_port = None

        for port, lst in dict_ports.items():
            lat = lst[0]
            if lat < min_cost:
                min_cost = lat
                key_port = port
        return key_port, min_cost

    #decrement every time the handler_time goes off
    def decrement_expiration_time(self):

        new_dv_table = {}
        for dst in self.dv_table:
            dict_ports = self.dv_table[dst]
            new_dict_ports = {}
            for port in dict_ports:
                lst = dict_ports[port]
                lat = lst[0]
                exp = lst[1]
                if lat == INFINITY:
                    continue
                if exp is None:
                    new_dict_ports[port] = [lat, exp]
                    continue
                exp -= self.DEFAULT_TIMER_INTERVAL
                if exp > 0:
                    new_dict_ports[port] = [lat, exp]
            if len(new_dict_ports) != 0:
                new_dv_table[dst] = new_dict_ports
        self.dv_table = new_dv_table


#count to infinity

#Keep in mind that you are allowed to send RoutePackets to hosts,
# but we will be testing you on sending excessive RoutePackets.
# This will be one of the potential places you can optimize,
# as sending RoutePackets to hosts doesn't do anything.
