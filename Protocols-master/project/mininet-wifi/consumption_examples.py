"""This example creates a simple network topology in which
   stations are equipped with batteries"""

from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.sixLoWPAN.node import OVSSensor
from mn_wifi.link import wmediumd, mesh


def topology():
    "Create a network."
    net = Mininet_wifi(iot_module='fakelb', apsensor=OVSSensor)
    # iot_module: fakelb or mac802154_hwsim
    # mac802154_hwsim is only supported from kernel 4.18

    info("*** Creating nodes\n")

    sta1 = net.addStation('sta1', mac='00:00:00:00:00:11', ip='10.0.0.1/8', position='40,180,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:12', ip='10.0.0.2/8', position='40,220,0')
    sta3 = net.addStation('sta3', mac='00:00:00:00:00:13', ip='90.0.0.3/8', position='450,290,0')

    apsensor1 = net.addAPSensor('apsensor1', wlans=4, ssid='ssid1, , ,', mode='g', ip='10.0.0.10/8', position='74,204,0', voltage=3.7, initialEnergy = 1000 , panid='0xbeef')
    apsensor2 = net.addAPSensor('apsensor2', wlans=4, ssid='ssid2, , ,', mode='g', ip='90.0.0.20/8', position='84,300,0', voltage=3.7, panid='0xbeef')
    apsensor3 = net.addAPSensor('apsensor3', ip='80.0.0.80/8', voltage=3.7, panid='0xbeef')

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Starting network\n")

    net.addLink(sta1,apsensor1)
    net.addLink(sta2,apsensor1)
    net.addLink(sta3,apsensor2) 

    
    net.plotGraph(max_x=500, max_y=500)  	

    net.build()
    
     
    
    info("*** Consumption information\n")
    print("apsensor1 : {}\n apsensor2 : {}\n apsensor3 : {} \n".format(apsensor1.wintfs[0].consumption, apsensor2.wintfs[0].consumption, apsensor3.wintfs[0].consumption))

    #print("apsensor1 : {}\n apsensor2 : {}\n apsensor3 : {} \n".format(apsensor1.wintfs[0].ip, apsensor2.wintfs[0].ip, apsensor3.wintfs[0].ip))

   # print(sensor1.getTotalEnergyConsumption)
    info("*** Running CLI\n")
    CLI(net)


    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()
