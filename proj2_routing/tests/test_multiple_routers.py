"""
Tests that hosts can connect to multiple routers.

Creates a topology like the following:

   s1 -- c1
  /        \ 
h1 -- c3 -- s3 -- h2
  \        /
   s2 -- c2

All links have cost 1.
When h1 pings h2, it should send the ping packet to all routers, and the same packet should arrive at h2 3 times.
In the other direction, h2 to h1, s3 should forward the packet directly to h1 (shortest path).

"""

import sim
import sim.api as api
import sim.basics as basics
import sys

from tests.test_simple import GetPacketHost, NoPacketHost
from tests.test_link_weights import CountingHub


def launch():
    h1 = GetPacketHost.create('h1')
    h2 = GetPacketHost.create('h2')

    s1 = sim.config.default_switch_type.create('s1')
    s2 = sim.config.default_switch_type.create('s2')
    s3 = sim.config.default_switch_type.create('s3')

    c1 = CountingHub.create('c1')
    c2 = CountingHub.create('c2')
    c3 = CountingHub.create('c3')

    h1.linkTo(s1)
    s1.linkTo(c1)
    c1.linkTo(s3)
    h1.linkTo(s2)
    s2.linkTo(c2)
    c2.linkTo(s3)
    h1.linkTo(c3)
    c3.linkTo(s3)
    s3.linkTo(h2)

    def test_tasklet():
        yield 15

        api.userlog.debug('Sending ping from h1 to h2 - it should hit 3 routers')
        h1.ping(h2)

        yield 5

        if h1.pings != 0 or h2.pings != 3 or c1.pings != 1 or c2.pings != 1 or c3.pings != 1:
            api.userlog.error("The ping did not propagate through all routers")
            sys.exit(1)

        api.userlog.debug('Sending ping from h2 to h1 - it should hit 1 router')
        h2.ping(h1)

        yield 5

        if h1.pings != 1 or h2.pings != 3 or c1.pings != 1 or c2.pings != 1 or c3.pings != 2:
            api.userlog.error("The ping hit more than 1 router")
            sys.exit(1)

        api.userlog.debug("Pings sent correctly")
        sys.exit(0)

    api.run_tasklet(test_tasklet)