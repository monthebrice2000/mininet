#sudo mn --custom ./custom_topo_wifi.py --topo mytopo --mac --switch ovsk --controller=remote,ip=127.0.0.1

from mn_wifi.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."
    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        sta1 = self.addStation( 'sta1' )
        sta2 = self.addStation( 'sta2' )
        sta3 = self.addStation( 'sta3' )
        sta4 = self.addStation( 'sta4' )
        sta5 = self.addStation( 'sta5' )
        sta6 = self.addStation( 'sta6' )
        sta7 = self.addStation( 'sta7' )
        sta8 = self.addStation( 'sta8' )
        ap9 = self.addAccessPoint( 'ap9' )
        ap10 = self.addAccessPoint( 'ap10' )
        ap11 = self.addAccessPoint( 'ap11' )
        ap12 = self.addAccessPoint( 'ap12' )
        ap13 = self.addAccessPoint( 'ap13' )

        # Add links
        self.addLink( sta1, ap9 )
        self.addLink( sta2, ap9 )
        self.addLink( sta3, ap9 )
        self.addLink( sta4, ap10 )
        self.addLink( sta5, ap11 )
        self.addLink( sta6, ap12 )
        self.addLink( sta7, ap13 )
        self.addLink( sta8, ap13 )
        self.addLink( ap9, ap10 )
        self.addLink( ap9, ap11 )
        self.addLink( ap10, ap13 )
        self.addLink( ap11, ap12 )
        self.addLink( ap11, ap13 )

#sudo mn --custom custom_example.py --topo mytopo
topos = { 'mytopo': ( lambda: MyTopo() ) }
