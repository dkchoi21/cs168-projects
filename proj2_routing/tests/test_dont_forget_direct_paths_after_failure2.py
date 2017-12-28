"""
Tests that direct routes are the default fallback, but eventually converges again.

Creates a topology like the following:

                    s3
                   / \
                  c2  \
                 /     \
h1 - s1 - c1 = s2 ===== h2
      \----------------/

1) Sends packet from h1 to h2, it should go through h1 - s1 - c1 - s2 - c2 - s3 - h2.
2) Take down the s2-s3 link. Send a packet from h1 before anything has a chance to update. It should send from h1 - s1 - c1 - s2 === h2.
3) Let the routing table converge. Send a packet from h1 to h2. It should send from h1 - s1 - h2.

"""

import sim
import sim.api as api
import sim.basics as basics

from tests.test_simple import GetPacketHost, NoPacketHost
from tests.test_link_weights import CountingHub

def launch():
    h1 = GetPacketHost.create('h1')
    h2 = GetPacketHost.create('h2')
    c1 = CountingHub.create('c1')
    c2 = CountingHub.create('c2')
    s1 = sim.config.default_switch_type.create('s1')
    s2 = sim.config.default_switch_type.create('s2')
    s3 = sim.config.default_switch_type.create('s3')

    h1.linkTo(s1, latency=1)
    s1.linkTo(c1, latency=6)
    c1.linkTo(s2, latency=6)
    s2.linkTo(h2, latency=5)
    s2.linkTo(c2, latency=1)
    c2.linkTo(s3, latency=1)
    s3.linkTo(h2, latency=1)
    h2.linkTo(s1, latency=10)
    
    def test_tasklet():
        yield 40

        api.userlog.debug('Sending ping from h1 to h2')
        h1.ping(h2)

        yield 20

        if c1.pings == 1 and c2.pings == 1 and h2.pings == 1:
            api.userlog.debug('The ping took the right path')
            good = True
        else:
            api.userlog.error('Wrong initial path!')
            good = False

        s2.unlinkTo(c2)
        s3.unlinkTo(c2)

        yield 0.1
        api.userlog.debug('Sending ping from h1 to h2')

        h1.ping(h2)
        yield 20
        if c1.pings == 2 and c2.pings == 1 and h2.pings == 2:
            api.userlog.debug('The ping took the right path')
            good = True and good
        else:
            api.userlog.error('Wrong, fallback direct path not used!')
            good = False

        yield 60
        api.userlog.debug('Sending ping from h1 to h2')

        h1.ping(h2)
        yield 20

        if c1.pings == 2 and h2.pings == 3:
            api.userlog.debug('Good path!')
            good = True and good
        else:
            api.userlog.error('%s, %s, %s', str(c1.pings), str(c2.pings), str(h2.pings))
            api.userlog.error('Paths not updated after fallback.')
            good = False
        import sys
        sys.exit(0 if good else 1)

    api.run_tasklet(test_tasklet)
