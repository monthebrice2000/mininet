#sudo mn --custom ./custom_topo.py --topo mytopo --mac --switch ovsk --controller=remote,ip=192.168.0.102

from mininet.topo import Topo

class MyTopo( Topo ):

    """

    # Data structure that must be inserted into the controller to represent this topology

    # Adjacency list of switches
    self.switches = {1: set([2,3,6,7,8]),
                     2: set([1,4,5,7]),
                     3: set([1,4,5,8]),
                     4: set([2,3,6,9]),
                     5: set([2,3,6,10]),
                     6: set([1,4,5,9,10]),
                     7: set([1,2]),
                     8: set([1,3]),
                     9: set([4,6]),
                     10: set([5,6])}

    # List of ports connecting other switches for each switch
    self.switches_ports = {1: {2: 2, 3: 3, 6: 4, 7: 5, 8: 6},
                           2: {1: 2, 4: 3, 5: 4, 7: 5},
                           3: {1: 2, 4: 3, 5: 4, 8: 5},
                           4: {2: 2, 3: 3, 6: 4, 9: 5},
                           5: {2: 2, 3: 3, 6: 4, 10: 5},
                           6: {1: 2, 4: 3, 5: 4, 9: 5, 10: 6},
                           7: {1: 2, 2: 3},
                           8: {1: 2, 3: 3},
                           9: {4: 2, 6: 3},
                           10: {5: 4, 6: 5}}

    self.ip_to_switch_port = dict({'10.0.0.1': [1,1],
                                   '10.0.0.2': [2,1],
                                   '10.0.0.3': [3,1],
                                   '10.0.0.4': [4,1],
                                   '10.0.0.5': [5,1],
                                   '10.0.0.6': [6,1],
                                   '10.0.0.7': [7,1],
                                   '10.0.0.8': [8,1],
                                   '10.0.0.9': [9,1],
                                   '10.0.0.10': [10,1],
                                   '10.0.0.11': [10,2],
                                   '10.0.0.12': [10,3]})

    # Switch DPID [ip1..ipn]
    self.switch_ips = dict({1:['10.0.0.1'],
                            2:['10.0.0.2'],
                            3:['10.0.0.3'],
                            4:['10.0.0.4'],
                            5:['10.0.0.5'],
                            6:['10.0.0.6'],
                            7:['10.0.0.7'],
                            8:['10.0.0.8'],
                            9:['10.0.0.9'],
                            10:['10.0.0.10','10.0.0.11','10.0.0.12']})
    """

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        h11 = self.addHost( 'h11' )
        h12 = self.addHost( 'h12' )
        h13 = self.addHost( 'h13' )
        h14 = self.addHost( 'h14' )
        h15 = self.addHost( 'h15' )
        h16 = self.addHost( 'h16' )
        h17 = self.addHost( 'h17' )
        h18 = self.addHost( 'h18' )
        h19 = self.addHost( 'h19' )
        h20 = self.addHost( 'h20' )
        h21 = self.addHost( 'h21' )
        h22 = self.addHost( 'h22' )
        s1 = self.addSwitch( 's1' )
        s2 = self.addSwitch( 's2' )
        s3 = self.addSwitch( 's3' )
        s4 = self.addSwitch( 's4' )
        s5 = self.addSwitch( 's5' )
        s6 = self.addSwitch( 's6' )
        s7 = self.addSwitch( 's7' )
        s8 = self.addSwitch( 's8' )
        s9 = self.addSwitch( 's9' )
        s10 = self.addSwitch( 's10' )

        # Add links
        self.addLink( h11, s1 )
        self.addLink( h12, s2 )
        self.addLink( h13, s3 )
        self.addLink( h14, s4 )
        self.addLink( h15, s5 )
        self.addLink( h16, s6 )
        self.addLink( h17, s7 )
        self.addLink( h18, s8 )
        self.addLink( h19, s9 )
        self.addLink( h20, s10 )
        self.addLink( h21, s10 )
        self.addLink( h22, s10 )
        self.addLink( s1, s2 )
        self.addLink( s1, s3 )
        self.addLink( s1, s6 )
        self.addLink( s1, s7 )
        self.addLink( s1, s8 )
        self.addLink( s2, s4 )
        self.addLink( s2, s5 )
        self.addLink( s2, s7 )
        self.addLink( s3, s4 )
        self.addLink( s3, s5 )
        self.addLink( s3, s8 )
        self.addLink( s4, s6 )
        self.addLink( s4, s9 )
        self.addLink( s5, s6 )
        self.addLink( s5, s10 )
        self.addLink( s6, s9 )
        self.addLink( s6, s10 )
        


topos = {
    'mytopo': ( lambda: MyTopo() )
}#
