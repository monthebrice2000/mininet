To make it properly works, first get familiar with mininet and openflow framework.

After running the initial tutorial of POX as remote controller for mininet, just overwrite the file
<path_to_pox>/pox/misc/of_tutorial.py. Now the controller provided here will be the controller of your
SDN.

Starting the controller:
cd <path_to_pox>
./pox.py log.level --DEBUG misc.of_tutorial
sudo mn --topo single,3 --mac --switch ovsk --controller=remote,ip=192.168.0.102

Controller with custom topology:
sudo mn --custom ./custom_topo.py --topo mytopo --mac --switch ovsk --controller=remote,ip=192.168.56.1

Note: this implementation assumes you are using the flag --mac while starting mininet.
Also, you must set the remote ip as the IP from br0 interface of the host computer.

Running the controller:
-In a new terminal, go to <path_to_pox>/pox/ and runs the command:
"$./pox.py log.level --DEBUG misc.random_paths"

Make sure to copy the file 'random_paths.py' to <path_to_pox>/pox/misc/

Important links:
-mininet walktrhough: http://mininet.org/walkthrough/
-openflow and pox: http://archive.openflow.org/wk/index.php/OpenFlow_Tutorial#Controller_Choice:_POX_.28Python.29
-pox: https://openflow.stanford.edu/display/ONL/POX+Wiki#POXWiki-OpenFlowinPOX
-pox learning switches: https://github.com/mininet/openflow-tutorial/wiki/Create-a-Learning-Switch

-https://github.com/CPqD/RouteFlow/blob/master/pox/pox/forwarding/l3_learning.py

-http://openvswitch.org/pipermail/discuss/2013-January/008784.html

Cannot convert argument to integer:
-http://t2650.network-pox-development.networktalks.us/adding-a-new-action-to-a-message-t2650.html

-https://openflow.stanford.edu/display/ONL/POX+Wiki

All paths between two links
-http://www.technical-recipes.com/2011/a-recursive-algorithm-to-find-all-paths-between-two-given-nodes/

DFS in python
-http://eddmann.com/posts/depth-first-search-and-breadth-first-search-in-python/



/** 
MONTHE
*/
./pox.py forwarding.l2_learning openflow.spanning_tree --no-flood --hold_down log.level --DEBUG samples.pretty_log openflow.discovery host_tracker info.packet_dump
./pox.py F2 log.level --DEBUG samples.pretty_log
./pox.py log.level --DEBUG  misc.F2 samples.pretty_log
sudo python meshRemoteControlWirelessNodesInformations.py
cd /home/esseai_mn/mininet-wifi



sudo ovs-ofctl dump-flows ap3

isinstance(packet, ipv4) // savoir si le paquet est une instance de ipv4
paquet.IP_TYPE
packet.next.srcip // addresse source IP d'un paquet 
paquet.next.dstip // adresse de destination IP d'un paquet
paquet.ARP_TYPE
paquet.payload.protosrc // addresse source IP d'un paquet 
paquet.payload.protodst // addresse destination IP d'un paquet
isinstance(packet, arp) // savoir si le paquet est une instance de arp
./pox.py forwarding.l3_learning --fakeways=10.0.0.1,192.168.0.1
h1 route add default gw 193.168.10.1
h2 route add default gw 192.167.50.1



je peux convertir la cni de l'ap en adresse MAC 
def dpid_to_mac(dpid):
    #je convertir la cni de l'ap en adresse MAC de l'ap ( MAC )
    return EthAddr("%012x" % (dpid & 0xffFFffFFffFF,))
