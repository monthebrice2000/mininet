#!/usr/bin/python

'This example shows how to create wireless mesh link between tens APs and seven stations'

from mininet.node import Controller, RemoteController
from mininet.log import setLogLevel, info
from mn_wifi.link import wmediumd, mesh
# from mn_wifi.cli import CLI_wifi
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference
from mn_wifi.node import OVSKernelAP, UserAP
from mn_wifi.energy import Energy


def topology():
    "Create a network."
    net = Mininet_wifi(controller=RemoteController, iot_module='fakelb', link=wmediumd, accessPoint=OVSKernelAP,
                       wmediumd_mode=interference)

    info("*** Creating nodes\n")
    nodes = []
    sta1 = net.addStation('sta1', mac='00:00:00:00:00:11', ip='10.0.0.1/8', position='40,180,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:12', ip='10.0.0.2/8', position='40,220,0')
    sta3 = net.addStation('sta3', mac='00:00:00:00:00:13', ip='90.0.0.3/8', position='450,290,0')
    sta4 = net.addStation('sta4', mac='00:00:00:00:00:14', ip='90.0.0.4/8', position='460,240,0')
    sta5 = net.addStation('sta5', mac='00:00:00:00:00:15', ip='80.0.0.5/8', position='420,110,0')
    sta6 = net.addStation('sta6', mac='00:00:00:00:00:16', ip='40.0.0.6/8', position='250,330,0')
    sta7 = net.addStation('sta7', mac='00:00:00:00:00:17', ip='20.0.0.7/8', position='60,320,0')

    ap1 = net.addAPSensor('ap1', wlans=4, ssid='ssid1, , ,', mode='g', ip='10.0.0.10/8', position='74,204,0', range=100,
                          voltage=3.7, panid='0xbeef')
    nodes.append(ap1)
    ap2 = net.addAPSensor('ap2', wlans=4, ssid='ssid2, , ,', mode='g', ip='20.0.0.20/8', position='84,300,0', range=100,
                          voltage=3.7, panid='0xbeef')
    nodes.append(ap2)
    ap3 = net.addAPSensor('ap3', wlans=4, ssid=', , ,', mode='g', ip='30.0.0.30/8', position='164,274,0', range=100,
                          voltage=3.7, panid='0xbeef')
    nodes.append(ap3)
    ap4 = net.addAPSensor('ap4', wlans=4, ssid='ssid4, , ,', mode='g', ip='40.0.0.40/8', position='244,300,0',
                          range=100, voltage=3.7, panid='0xbeef')
    nodes.append(ap4)
    ap5 = net.addAPSensor('ap5', wlans=4, ssid=', , ,', mode='g', ip='50.0.0.50/8', position='224,174,0', range=100,
                          voltage=3.7, panid='0xbeef')
    nodes.append(ap5)
    ap6 = net.addAPSensor('ap6', wlans=4, ssid='ssid6, , ,', mode='g', ip='60.0.0.60/8', position='304,154,0',
                          range=100, voltage=3.7, panid='0xbeef')
    nodes.append(ap6)
    ap7 = net.addAPSensor('ap7', wlans=4, ssid='ssid7, , ,', mode='g', ip='70.0.0.70/8', position='340,274,0',
                          range=100, voltage=3.7, panid='0xbeef')
    nodes.append(ap7)
    ap8 = net.addAPSensor('ap8', wlans=4, ssid='ssid8, , ,', mode='g', ip='80.0.0.80/8', position='420,144,0',
                          range=100, voltage=3.7, panid='0xbeef')
    nodes.append(ap8)
    ap9 = net.addAPSensor('ap9', wlans=4, ssid='ssid9, , ,', mode='g', ip='90.0.0.90/8', position='420,264,0',
                          range=100, voltage=3.7, panid='0xbeef')
    nodes.append(ap9)
    ap10 = net.addAPSensor('ap10', wlans=4, ssid='ssid2, , ,', mode='g', ip='100.0.0.100/8', position='144,114,0',
                           range=100, voltage=3.7, panid='0xbeef')
    nodes.append(ap10)

    c0 = net.addController('c0', controller=RemoteController, ip='0.0.0.0', protocol='tcp', port=6633)

    net.setPropagationModel(model="logDistance", exp=4)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Associating Stations\n")
    net.addLink(sta1, ap1)
    net.addLink(sta2, ap1)
    net.addLink(sta3, ap9)
    net.addLink(sta4, ap9)
    net.addLink(sta5, ap8)
    net.addLink(sta6, ap4)
    net.addLink(sta7, ap2)



    net.addLink(ap1, ap2)
    net.addLink(ap1, ap3)
    net.addLink(ap1, ap10)
    net.addLink(ap2, ap3)
    net.addLink(ap10, ap5)
    net.addLink(ap3, ap5)
    net.addLink(ap3, ap4)
    net.addLink(ap5, ap6)
    net.addLink(ap5, ap4)
    net.addLink(ap4, ap7)
    net.addLink(ap7, ap6)
    net.addLink(ap6, ap8)
    net.addLink(ap7, ap9)
    net.addLink(ap8, ap9)

    net.plotGraph(max_x=500, max_y=500)

    info("*** Starting network\n")
    net.build()
    c0.start()
    ap1.start([c0])
    ap2.start([c0])

    info("nombres de aps et de controlleurs\n")
    info(len(net.controllers), " controllers ", len(net.aps), " aps", len(net.stations), " stations\n");

    info("Traitement de l'energie")
    Energy( nodes )
    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    # net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()
