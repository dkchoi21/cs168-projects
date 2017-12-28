"""
Performs various tests on the given *rand* topology.

"""

import sim
import sim.api as api
import topos.rand as topo_rand
import sys

from tests.test_simple import GetPacketHost


def launch():
    host_count = 4
    topo_rand.launch(host_type=GetPacketHost, hosts=host_count)

    def test_tasklet():
        yield 20
        # when i drop this number to '15' i seldomly start getting test failures
        # let me know if you have the same problem

        h1.ping(h2)
        h1.ping(h3)
        h1.ping(h4)

        h2.ping(h1)
        h2.ping(h3)
        h2.ping(h4)

        h3.ping(h1)
        h3.ping(h2)
        h3.ping(h4)

        h4.ping(h1)
        h4.ping(h2)
        h4.ping(h3)

        yield 10
       
        if h1.pings != 3 or h2.pings != 3 or h3.pings != 3 or h4.pings != 3:
            api.userlog.error("The pings didn't get through")
            sys.exit(1)
        
        api.userlog.debug("Pings got through")
        sys.exit(0)

    api.run_tasklet(test_tasklet)