from mininet.net import Mininet
from mininet.node import Controller,RemoteController
from mn_wifi.node import OVSKernelAP
from mn_wifi.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink

from mininet.node import Controller, RemoteController
from mininet.log import setLogLevel, info
from mn_wifi.link import wmediumd, mesh
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference


def topology():
    "Create a network."
    net = Mininet(controller=Controller, link=TCLink, accessPoint=OVSKernelAP,
                  enable_wmediumd=True, enable_interference=True)

    print
    "*** Creating nodes"
    sta1 = net.addStation('sta1', mac='00:00:00:00:00:11', ip="192.168.0.1/24")
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:12', ip="192.168.0.2/24")
    sta3 = net.addStation('sta3', mac='00:00:00:00:00:13', ip="192.168.0.3/24")
    sta4 = net.addStation('sta4', mac='00:00:00:00:00:14', ip="192.168.0.4/24")
    ap1 = net.addAccessPoint('ap1', wlans=2, ssid='ssid1,', position='10,10,0')
    ap2 = net.addAccessPoint('ap2', wlans=2, ssid='ssid2,', position='30,10,0')
    ap3 = net.addAccessPoint('ap3', wlans=2, ssid='ssid3,', position='50,10,0')
    c0 = net.addController('c0', controller=Controller)

    print
    "*** Configuring wifi nodes"
    net.configureWifiNodes()

    print
    "*** Associating Stations"
    # net.addLink(sta4, ap1)
    net.addLink(sta1, ap1)
    net.addLink(sta2, ap2)
    net.addLink(sta3, ap3)
    net.addMesh(ap1, intf='ap1-wlan2', ssid='mesh-ssid1')
    net.addMesh(ap2, intf='ap2-wlan1', ssid='mesh-ssid1')
    net.addMesh(ap2, intf='ap2-wlan2', ssid='mesh-ssid2')
    net.addMesh(ap3, intf='ap3-wlan2', ssid='mesh-ssid2')

    print
    "*** Starting network"
    net.build()
    c0.start()
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])

    print
    "*** Running CLI"
    CLI(net)

    print
    "*** Stopping network"
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()