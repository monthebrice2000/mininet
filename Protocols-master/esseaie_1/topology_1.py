from mn_wifi.net import Mininet_wifi
from mn_wifi.cli import CLI_wifi
from mininet.node import RemoteController
from mininet.log import setLogLevel, info

def topology():
    "Create a network."
    net = Mininet_wifi(controller=RemoteController)

    info("*** Creating nodes\n")
    c1 = net.addController('c1', ip='127.0.0.1', port=6633)
    ap2 = net.addAccessPoint('ap2', ssid='new-ssid2', mode='g', channel='1',
                             position='216.2,141,0', range=100, protocols='OpenFlow10')
    s3 = net.addSwitch('s3', protocols='OpenFlow10', listenPort=6674, mac='00:00:00:00:00:03')
    h4 = net.addHost('h4', mac='00:00:00:00:00:04', ip='10.0.0.4/8')
    sta5 = net.addStation('sta5', wlans=1, mac='00:00:00:00:00:05', ip='10.0.0.5/8',
                          position='165.25,141,0', range=18)

    info("*** Creating links\n")
    net.addLink(ap2, s3)
    net.addLink(s3, h4)
    net.addLink( ap2, sta5 )

    info("*** Starting network\n")
    net.configureWifiNodes()

    net.plotGraph(min_x=50, min_y=50, max_x=599, max_y=599)

    net.build()
    c1.start()
    s3.start([c1])
    ap2.start([c1])

    info("*** Running CLI\n")
    CLI_wifi(net)

    info("*** Stopping network\n")
    net.stop()



if name == 'main':
    setLogLevel( 'info' )
    topology()