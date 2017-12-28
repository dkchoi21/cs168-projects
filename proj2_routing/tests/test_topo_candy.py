"""
Performs various tests on the given *candy* topology.

It looks like:

    h1a    s4--s5    h2a
       \  /      \  /
        s1        s2
       /  \      /  \ 
    h1b    --s3--    h2b

"""

import sim
import sim.api as api
import topos.candy as candy
import sys

from tests.test_simple import GetPacketHost

def launch():
    candy.launch(host_type=GetPacketHost)

    def test_tasklet():
        yield 12

        api.userlog.debug('Sending multiple pings - all should get through')
        h1a.ping(h2b)
        h1a.ping(h1b)
        h1b.ping(h2a)
        h1b.ping(h1a)
        h2a.ping(h1b)
        h2a.ping(h2b)
        h2b.ping(h1a)
        h2b.ping(h2a)

        yield 5

        if h1a.pings != 2 or h1b.pings != 2 or h2a.pings != 2 or h2b.pings != 2:
            api.userlog.error("The pings didn't get through")
            sys.exit(1)
        
        api.userlog.debug("First round of pings got through")

        api.userlog.debug('Disconnecting s1 and s3')
        s1.unlinkTo(s3)

        yield 12

        api.userlog.debug('Sending same set of pings again - all should get through')
        h1a.ping(h2b)
        h1a.ping(h1b)
        h1b.ping(h2a)
        h1b.ping(h1a)
        h2a.ping(h1b)
        h2a.ping(h2b)
        h2b.ping(h1a)
        h2b.ping(h2a)

        yield 7

        if h1a.pings != 4 or h1b.pings != 4 or h2a.pings != 4 or h2b.pings != 4:
            api.userlog.error("The pings didn't get through")
            sys.exit(1)
        
        api.userlog.debug("Second round of pings got through")
        sys.exit(0)

    api.run_tasklet(test_tasklet)