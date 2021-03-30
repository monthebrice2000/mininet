#sudo mn --custom ./custom_topo_new.py --topo mytopo --mac --switch ovsk --controller=remote,ip=192.168.0.102

from mininet.topo import Topo

class MyTopo( Topo ):

    """

    # Data structure that must be inserted into the controller to represent this topology

    # Adjacency list of switches
    self.switches = {9: set([10,11]),
                     10: set([9,13]),
                     11: set([9,12,13]),
                     12: set([11]),
                     13: set([10,11])}

    # List of ports connecting other switches for each switch
    self.switches_ports = {
                            9: {10: 4, 11: 5},
                           10: {9: 2, 13: 3},
                           11: {9: 2, 12: 3, 13: 4},
                           12: {11: 2},
                           13: {10: 3, 11: 4}
                          }

    self.ip_to_switch_port = dict({
                                    '10.0.0.1': [9,1],
                                   '10.0.0.2': [9,2],
                                   '10.0.0.3': [9,3],
                                   '10.0.0.4': [10,1],
                                   '10.0.0.5': [11,1],
                                   '10.0.0.6': [12,1],
                                   '10.0.0.7': [13,1],
                                   '10.0.0.8': [13,2]
                                 })

    # Switch DPID [ip1..ipn]
    self.switch_ips = dict({
                            9:['10.0.0.1','10.0.0.2', '10.0.0.3'],
                            10:['10.0.0.4'],
                            11:['10.0.0.5'],
                            12:['10.0.0.6'],
                            13:['10.0.0.7','10.0.0.8']
                        })
    """

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
        h3 = self.addHost( 'h3' )
        h4 = self.addHost( 'h4' )
        h5 = self.addHost( 'h5' )
        h6 = self.addHost( 'h6' )
        h7 = self.addHost( 'h7' )
        h8 = self.addHost( 'h8' )
        s9 = self.addSwitch( 's9' )
        s10 = self.addSwitch( 's10' )
        s11 = self.addSwitch( 's11' )
        s12 = self.addSwitch( 's12' )
        s13 = self.addSwitch( 's13' )

        # Add links
        self.addLink( h1, s9 )
        self.addLink( h2, s9 )
        self.addLink( h3, s9 )
        self.addLink( h4, s10 )
        self.addLink( h5, s11 )
        self.addLink( h6, s12 )
        self.addLink( h7, s13 )
        self.addLink( h8, s13 )
        self.addLink( s9, s10 )
        self.addLink( s9, s11 )
        self.addLink( s10, s13 )
        self.addLink( s11, s12 )
        self.addLink( s11, s13 )


topos = { 'mytopo': ( lambda: MyTopo() ) }
