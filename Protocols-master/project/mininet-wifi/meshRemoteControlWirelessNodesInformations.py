!/usr/bin/python

'This example shows how to create wireless mesh link between tens APs and seven stations'

from mininet.node import Controller, RemoteController
from mininet.log import setLogLevel, info
from mn_wifi.link import wmediumd, mesh
#from mn_wifi.cli import CLI_wifi
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference
from mn_wifi.node import OVSKernelAP, UserAP

import random
import time
from SDS_Controller import SDVanet_Controller
from SDS1 import SDStor_Ap
from SDS_RSU import SD_RSU
from config import Modes

SD_Ap = SDStor_Ap
VANET_Controller = SDVanet_Controller
RSU = SD_RSU

def topology():
    "Create a network."
    net = Mininet_wifi(controller= RemoteController,iot_module='fakelb', link=wmediumd, accessPoint=SD_Ap,
                       wmediumd_mode=interference)

    info("*** Creating nodes\n")
    sta1 = net.addStation('sta1', mac='00:00:00:00:00:11', ip='10.0.0.2/8', defaultRoute="via 10.0.0.1",
                          position='40,180,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:12', ip='10.0.0.3/8', defaultRoute="via 10.0.0.1",
                          position='40,220,0')
    sta3 = net.addStation('sta3', mac='00:00:00:00:00:13', ip='90.0.0.4/8', defaultRoute="via 90.0.0.1",
                          position='450,290,0')
    sta4 = net.addStation('sta4', mac='00:00:00:00:00:14', ip='90.0.0.5/8', defaultRoute="via 90.0.0.1",
                          position='460,240,0')
    sta5 = net.addStation('sta5', mac='00:00:00:00:00:15', ip='80.0.0.6/8', defaultRoute="via 80.0.0.1",
                          position='420,110,0')
    sta6 = net.addStation('sta6', mac='00:00:00:00:00:16', defaultRoute="via 40.0.0.1", ip='40.0.0.7/8',
                          position='250,330,0')
    sta7 = net.addStation('sta7', mac='00:00:00:00:00:17', defaultRoute="via 20.0.0.1", ip='20.0.0.8/8',
                          position='60,320,0')
    info("*** creation des access points\n")
    ap1 = net.addAPSensor('ap1', wlans=4, ssid='ssid1', mode='g', ip='10.0.0.1/8', position='74,204,0' ,range=100 ,voltage=3.7, panid='0xbeef', cls=RSU)
    ap2 = net.addAPSensor('ap2', wlans=4, ssid='ssid2', mode='g', ip='20.0.0.1/8', position='84,300,0' ,range=100 , voltage=3.7, panid='0xbeef',cls=RSU)
    ap3 = net.addAPSensor('ap3', wlans=4, ssid='ssid3', mode='g', ip='30.0.0.1/8', position='164,274,0' ,range=100 , voltage=3.7, panid='0xbeef',cls=RSU)
    ap4 = net.addAPSensor('ap4', wlans=4, ssid='ssid4', mode='g', ip='40.0.0.1/8', position='244,300,0' ,range=100 , voltage=3.7, panid='0xbeef',cls=RSU)
    ap5 = net.addAPSensor('ap5', wlans=4, ssid='ssid5', mode='g', ip='50.0.0.1/8', position='224,174,0' ,range=100 , voltage=3.7, panid='0xbeef',cls=RSU)
    ap6 = net.addAPSensor('ap6', wlans=4, ssid='ssid6', mode='g', ip='60.0.0.1/8', position='304,154,0' ,range=100 , voltage=3.7, panid='0xbeef',cls=RSU)
    ap7 = net.addAPSensor('ap7', wlans=4, ssid='ssid7', mode='g', ip='70.0.0.1/8', position='340,274,0' ,range=100 , voltage=3.7, panid='0xbeef',cls=RSU)
    ap8 = net.addAPSensor('ap8', wlans=4, ssid='ssid8', mode='g', ip='80.0.0.1/8', position='420,144,0' ,range=100 , voltage=3.7, panid='0xbeef',cls=RSU)
    ap9 = net.addAPSensor('ap9', wlans=4, ssid='ssid9', mode='g', ip='90.0.0.1/8', position='420,264,0' ,range=100 , voltage=3.7, panid='0xbeef',cls=RSU)
    ap10 = net.addAPSensor('ap10', wlans=4, ssid='ssid10', mode='g', ip='100.0.0.1/8',range=100 , voltage=3.7, panid='0xbeef',cls=RSU, position='144,114,0' )

    info("*** creation du controller\n")
    c0 = net.addController('c0', controller=RemoteController, ip='0.0.0.0', protocol='tcp', port=6633)

    net.setPropagationModel(model="logDistance", exp=4)


    def SDStorage(datasize):
        start2 = time.time()
        datasize = int(datasize)
        print ("car %s want to store %s bytes" % (0, datasize))
        #car[0].store(datasize,Modes.MEC, net)
        end2 = time.time()
        with open('Storage.txt', 'a') as f:
            f.write('%.12f \n' % (end2-start2))
        print ("took : ", end2 - start2)
        

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()
   

    info("*** Associating Stations\n")
    net.addLink(sta1,ap1)
    net.addLink(sta2,ap1)
    net.addLink(sta3,ap9)
    net.addLink(sta4,ap9)
    net.addLink(sta5,ap8)
    net.addLink(sta6,ap4)
    net.addLink(sta7,ap2)

   
    info("*** Creating mesh links\n")
    net.addLink(ap1, intf='ap1-wlan2', cls=mesh, ssid='meshNet12', mode='g', channel=5)
    net.addLink(ap2, intf='ap2-wlan2', cls=mesh, ssid='meshNet12', mode='g', channel=5)

    net.addLink(ap1, intf='ap1-wlan3', cls=mesh, ssid='meshNet13', mode='g', channel=5)
    net.addLink(ap3, intf='ap3-wlan1', cls=mesh, ssid='meshNet13', mode='g', channel=5)

    net.addLink(ap1, intf='ap1-wlan4', cls=mesh, ssid='meshNet110', mode='g', channel=5)
    net.addLink(ap10, intf='ap10-wlan2', cls=mesh, ssid='meshNet110', mode='g', channel=5)

    net.addLink(ap2, intf='ap2-wlan3', cls=mesh, ssid='meshNet23', mode='g', channel=5)
    net.addLink(ap3, intf='ap3-wlan2', cls=mesh, ssid='meshNet23', mode='g', channel=5)
    net.addLink(ap5, intf='ap5-wlan1', cls=mesh, ssid='meshNet510', mode='g', channel=5)
    net.addLink(ap10, intf='ap10-wlan3', cls=mesh, ssid='meshNet510', mode='g', channel=5)
    net.addLink(ap3, intf='ap3-wlan3', cls=mesh, ssid='meshNet35', mode='g', channel=5)
    net.addLink(ap5, intf='ap5-wlan2', cls=mesh, ssid='meshNet35', mode='g', channel=5)
    net.addLink(ap3, intf='ap3-wlan4', cls=mesh, ssid='meshNet34', mode='g', channel=5)
    net.addLink(ap4, intf='ap4-wlan2', cls=mesh, ssid='meshNet34', mode='g', channel=5)
    net.addLink(ap4, intf='ap4-wlan3', cls=mesh, ssid='meshNet45', mode='g', channel=5)
    net.addLink(ap5, intf='ap5-wlan3', cls=mesh, ssid='meshNet45', mode='g', channel=5)
    net.addLink(ap5, intf='ap5-wlan4', cls=mesh, ssid='meshNet56', mode='g', channel=5)
    net.addLink(ap6, intf='ap6-wlan2', cls=mesh, ssid='meshNet56', mode='g', channel=5)
    net.addLink(ap4, intf='ap4-wlan4', cls=mesh, ssid='meshNet47', mode='g', channel=5)
    net.addLink(ap7, intf='ap7-wlan2', cls=mesh, ssid='meshNet47', mode='g', channel=5)
    net.addLink(ap6, intf='ap6-wlan3', cls=mesh, ssid='meshNet67', mode='g', channel=5)
    net.addLink(ap7, intf='ap7-wlan3', cls=mesh, ssid='meshNet67', mode='g', channel=5)
    net.addLink(ap6, intf='ap6-wlan4', cls=mesh, ssid='meshNet68', mode='g', channel=5)
    net.addLink(ap8, intf='ap8-wlan2', cls=mesh, ssid='meshNet68', mode='g', channel=5)
    net.addLink(ap7, intf='ap7-wlan4', cls=mesh, ssid='meshNet79', mode='g', channel=5)
    net.addLink(ap9, intf='ap9-wlan2', cls=mesh, ssid='meshNet79', mode='g', channel=5)
    net.addLink(ap8, intf='ap8-wlan3', cls=mesh, ssid='meshNet89', mode='g', channel=5)
    net.addLink(ap9, intf='ap9-wlan3', cls=mesh, ssid='meshNet89', mode='g', channel=5)
    
    net.addLink(ap1,ap2)
    net.addLink(ap1,ap3)
    net.addLink(ap1,ap10)
    net.addLink(ap2,ap3)
    net.addLink(ap10,ap5)
    net.addLink(ap3,ap5)
    net.addLink(ap3,ap4)
    net.addLink(ap5,ap6)
    net.addLink(ap5,ap4)
    net.addLink(ap4,ap7)
    net.addLink(ap7,ap6)
    net.addLink(ap6,ap8)
    net.addLink(ap7,ap9)
    net.addLink(ap8,ap9)

   
    net.plotGraph(max_x=500, max_y=500)


    info('*** Starting network\n')
    info('*** Starting net.build\n')
    net.build()
    info('*** After net.build()\n')
    c0.start()
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])
    ap4.start([c0])
    ap5.start([c0])
    ap6.start([c0])
    ap7.start([c0])
    ap8.start([c0])
    ap9.start([c0])
    ap10.start([c0])
    info("*** Finishing build network\n")
    print ("Draw 10 roads and place the 4 MEC nodes along them?")
    print ("\n\n\n***************************START*******************************")
    #datasize = raw_input("What is the amount of storage you want (in bytes)")
    #SDStorage(datasize)
    print ("\n\n\n***************************END*******************************")
    print ("(MEC) info Table after the test")
    #net.aps[0].listMecContents(Modes.MEC, net)
    print ("\n\n\n***************************TEST*******************************")
    print ("CAPACITY OF MEMORY\n\n")
    #print(c0.get_capacity(ap1, "ap"))
    x = float(ap1.capacity)/1024
    print(str(x)+" Mo")


    info("*** Running CLI\n")
    info('*** Start running CLI function\n')
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()
