"""
Tests that direct routes are the default fallback.

Creates a topology like the following:

h1 == s1 -- h2
  \      \           
    c1 --  s3

Sends packet from h2 to h1, c1 should be triggered. disconnect s1 and s3. s1 should remember that it can reach h1 directly
so h1 will still be reached without c1 being touched. 
"""

import sim
import sim.api as api
import sim.basics as basics

from tests.test_simple import GetPacketHost, NoPacketHost
from tests.test_link_weights import CountingHub

def launch():
    h2 = NoPacketHost.create('h2')
    h1 = GetPacketHost.create('h1')

    s1 = sim.config.default_switch_type.create('s1')
    s3 = sim.config.default_switch_type.create('s3')
    c1 = CountingHub.create('c1')
    h1.linkTo(s1, latency=10)
    s1.linkTo(s3, latency=1)
    s1.linkTo(h2, latency=1)
    h1.linkTo(c1, latency=1)
    c1.linkTo(s3, latency=1)

    def test_tasklet():
        yield 15

        api.userlog.debug('Sending ping from h2 to h1')
        h2.ping(h1)

        yield 5

        if c1.pings == 1:
            api.userlog.debug('The ping took the right path')
            good = True
        else:
            api.userlog.error('Wrong initial path!')
            good = False
        s1.unlinkTo(s3)

        yield 0.1
        api.userlog.debug('Sending ping from h2 to h1')

        h2.ping(h1)
        yield 15
        if c1.pings == 1 and h1.pings == 2:
        	api.userlog.debug('Good path!')
        	good = True and good 
        else:
        	api.userlog.error('Wrong, fallback direct path not used!')
        	good = False
        
        import sys
        sys.exit(0 if good else 1)

    api.run_tasklet(test_tasklet)