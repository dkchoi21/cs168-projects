"""
Tests the count to infinity example from the FAQ.
Link: https://github.com/NetSys/cs168fall17_student/blob/master/projects/proj2_routing/faq.md#what-is-an-example-of-count-to-infinity

Creates a topology like the following:

                d -- H_d
             // |
H_a -- a -- b   |
              \ |
                c -- H_c

> b-d and b-c and c-d have packet counting hubs in between which are not shown above.

All links have cost 1 except the link b-d which has cost 1.5.
We wait for routes to converge. Initially  both H_c and H_d can reach H_a.
We then fail the link a-b.
After sufficient time to count to infinity pings should be dropped at routers c & d without being sent to b.
Update: resolve the asymmetry of the CountingHub links.

"""

import sim
import sim.api as api
import sim.basics as basics
import sys

from tests.test_simple import GetPacketHost, NoPacketHost
# from tests.test_link_weights import CountingHub


class CountingHubWithLatency(api.Entity):
    pings = 0
    latency = 0

    def set_lat(self, latency):
        self.latency = latency

    def handle_rx(self, packet, in_port):
        if isinstance(packet, basics.RoutePacket):
            packet.latency += self.latency
        self.send(packet, in_port, flood=True)
        if isinstance(packet, basics.Ping):
            api.userlog.debug('%s saw a ping' % (self.name, ))
            self.pings += 1


def launch():
    h_a = GetPacketHost.create('h_a')
    h_c = NoPacketHost.create('h_c')
    h_d = NoPacketHost.create('h_d')

    backup_interval = sim.config.default_switch_type.DEFAULT_TIMER_INTERVAL
    sim.config.default_switch_type.DEFAULT_TIMER_INTERVAL = 1
    a = sim.config.default_switch_type.create('a')
    b = sim.config.default_switch_type.create('b')
    c = sim.config.default_switch_type.create('c')
    d = sim.config.default_switch_type.create('d')

    c_cb = CountingHubWithLatency.create('c_cb')
    c_cb.set_lat(0.5)
    c_db = CountingHubWithLatency.create('c_db')
    c_db.set_lat(0.75)
    c_cd = CountingHubWithLatency.create('c_cd')
    c_cd.set_lat(0.5)

    h_a.linkTo(a)
    h_c.linkTo(c)
    h_d.linkTo(d)

    a.linkTo(b)
    b.linkTo(c_cb, latency=0.5)
    b.linkTo(c_db, latency=0.75)
    c_cb.linkTo(c, latency=0.5)
    c_db.linkTo(d, latency=0.75)
    c.linkTo(c_cd, latency=0.5)
    c_cd.linkTo(d, latency=0.5)

    def test_tasklet():
        yield 15

        api.userlog.debug('Sending ping from h_c to h_a - it should get through')
        h_c.ping(h_a)

        yield 6

        if h_a.pings != 1 or c_cb.pings != 1 or c_cd.pings != 0:
            api.userlog.error("The first ping didn't get through or followed wrong path")
            sys.exit(1)

        api.userlog.debug('Sending ping from h_d to h_a - it should get through')
        h_d.ping(h_a)

        yield 6

        if h_a.pings != 2 or c_db.pings != 1 or c_cd.pings != 0:
            api.userlog.error("The second ping didn't get through or followed wrong path")
            sys.exit(1)

        api.userlog.debug('Disconnecting a and b')
        a.unlinkTo(b)

        api.userlog.debug('Waiting for routers to count to infinity')
        yield 5
        #changed it from yield 10 to yield 5 and it works now -->weird

        api.userlog.debug(
            'Sending ping from h_c to h_a - it should be dropped at c')
        h_c.ping(h_a)

        yield 5

        if c_cb.pings != 1 or c_cd.pings != 0:
            api.userlog.error(
                'c forwarded the ping when it should have dropped it')
            sys.exit(1)
        else:
            api.userlog.debug('c dropped the ping as expected')
            sys.exit(0)

    api.run_tasklet(test_tasklet)
    sim.config.default_switch_type.DEFAULT_TIMER_INTERVAL = backup_interval