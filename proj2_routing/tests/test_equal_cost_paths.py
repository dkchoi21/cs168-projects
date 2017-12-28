"""
Tests that once an equal cost path goes down, the alternative is used immediately.

Creates a topology like the following:

        c2 -- s2
        /        \ 
h1 -- s1          h2
        \        /
        c3 -- s3

All links have cost 1.
When h1 pings h2, s1 could send the packet on either path.
We then start blocking routing packets between s1-s2 (or s1-s3 if thats the path the first ping took).
The route through the blocked router should eventually expire and ping packets headed to h2 should use the other path.
This test makes sure that this switching happens and packets don't get dropped.

"""

import sim
import sim.api as api
import sim.basics as basics
import sys

from tests.test_simple import GetPacketHost, NoPacketHost
from tests.test_link_weights import CountingHub

class BlockingHub(CountingHub):
    block_route_packets = False

    def handle_rx(self, packet, in_port):
        if isinstance(packet, basics.RoutePacket):
            if self.block_route_packets:
                src = api.get_name(packet.src)
                api.userlog.debug('%s dropped a route packet from %s' % (self.name, src))
                return
        return super(BlockingHub, self).handle_rx(packet, in_port)

def launch():
    h1 = NoPacketHost.create('h1')
    h2 = GetPacketHost.create('h2')

    s1 = sim.config.default_switch_type.create('s1')
    s2 = sim.config.default_switch_type.create('s2')
    s3 = sim.config.default_switch_type.create('s3')

    c2 = BlockingHub.create('c2')
    c3 = BlockingHub.create('c3')

    h1.linkTo(s1)
    s1.linkTo(c2)
    c2.linkTo(s2)
    s2.linkTo(h2)
    s1.linkTo(c3)
    c3.linkTo(s3)
    s3.linkTo(h2)

    def test_tasklet():
        yield 15

        api.userlog.debug('Sending ping from h1 to h2 - it should get through')
        h1.ping(h2)

        yield 5

        if h2.pings != 1:
            api.userlog.error("The ping did not get through to h2")
            sys.exit(1)
        
        if c2.pings == 1:
            api.userlog.debug('Ping was sent through s2, dropping routing packets between s1-s2')
            c2.block_route_packets = True
        elif c3.pings == 1:
            api.userlog.debug('Ping was sent through s3, dropping routing packets between s1-s3')
            c3.block_route_packets = True
        else:
            api.userlog.error('Something wierd happened')

        yield sim.config.default_switch_type.ROUTE_TIMEOUT - 1
        # '-1' since the link h1-s1 has latency 1
        # if the test fails for you, try removing this '-1', not sure if it is nitpicking

        api.userlog.debug('Sending another ping from h1 to h2 - it should take the other path')
        h1.ping(h2)

        yield 5

        if h2.pings != 2 or c2.pings != 1 or c3.pings != 1:
            api.userlog.error("The second ping did not take the correct path")
            sys.exit(1)

        api.userlog.debug("Paths expired and replaced correctly")
        sys.exit(0)

    api.run_tasklet(test_tasklet)