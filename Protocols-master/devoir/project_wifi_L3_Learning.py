from pox.lib.revent import *
from pox.lib.packet.arp import arp
from pox.lib.addresses import IPAddr, EthAddr
import pox.openflow.discovery
import pox.openflow.libopenflow_01 as of
from pox.core import core
from pox.lib.packet.ethernet import ethernet, ETHER_BROADCAST
from pox.lib.util import dpid_to_str, str_to_bool
from pox.lib.revent import EventHalt, Event, EventMixin
log = core.getLogger()

IDLE_TIMEOUT = 100
HARD_TIMEOUT = 300
IP_TYPE = 0x800
ARP_TYPE = 0x806

#variable pour staocker l'arbre de la topologie
switches = {}
#variable pour staosker l'arbre de la topologie a
# ainsi que les ports aui relient les aps
switches_ports = {}
#variable pour stocker les aps ainsi leur dpid
switches_dpids = {}

def add_in_switches_dpid( dpid1, dpid2 ):
    """
    Cette fonction permet de stocker le dpid d'in ap dans la variable switches_dpids
    """
    switches_dpids[ "ap"+dpid_to_str( dpid1 )[16] ] = dpid1
    switches_dpids[ "ap"+dpid_to_str( dpid2 )[16] ] = dpid2

def add_in_switches(dpid1, port1, dpid2, port2):
    """
    Cette fonction permet d'ajouter les aps dans l'arbre de la topologie
    representée par la variable switchers
    """
    if "ap" + dpid_to_str(dpid1)[16] in switches:
        switches["ap" + dpid_to_str(dpid1)[16] ].add("ap" + dpid_to_str(dpid2)[16])
    else:
        switches["ap" + dpid_to_str(dpid1)[16]] = set(["ap" + dpid_to_str(dpid2)[16]])

def add_in_switches_ports(dpid1, port1, dpid2, port2):
    """
    Cette fonction permet de stacker le port qui relie l'ap2 de dpid2 à l'ap1 de dpid1
    """
    if 'ap' + dpid_to_str(dpid1)[16] in switches_ports:
        switches_ports['ap' + dpid_to_str(dpid1)[16]]['ap' + dpid_to_str(dpid2)[16]] = port1
    else:
        switches_ports['ap' + dpid_to_str(dpid1)[16]] = {}
        switches_ports['ap' + dpid_to_str(dpid1)[16]]['ap' + dpid_to_str(dpid2)[16]] = port1

def get_min_path( paths ):
    """
    Cette fonction permet de retrouver le chemin optimal
    à partir de la liste des chemins possibles
    """
    path = []
    if( len(paths) == 0 ):
        return path
    path = paths[0]
    for path_in in paths:
        if len(path) > len( path_in ):
            path = path_in
    return path

def send_arp_reply(reply_to, mac, src_mac=None):
    """
    Send an ARP reply.

    reply_to is a PacketIn event corresponding to an ARP request

    mac is the MAC address to reply with

    src_mac is the MAC address that the reply comes from (the L2 address)

    mac and src_mac can be EthAddrs, or the following special values:
      False - use the "DPID MAC" (MAC based on switch DPID)
      True  - use the MAC of the port the event was received by

    Additionally, src_mac can be None (the default), which means to use
    the same value as mac.
    """
    if mac is False:
        mac = reply_to.connection.eth_addr
    elif mac is True:
        mac = reply_to.connection.ports[reply_to.port].hw_addr
    mac = EthAddr(mac)
    if src_mac is None:
        src_mac = mac
    elif src_mac is False:
        src_mac = reply_to.connection.eth_addr
    elif src_mac is True:
        src_mac = reply_to.connection.ports[reply_to.port].hw_addr
    src_mac = EthAddr(src_mac)
    arpp = reply_to.parsed.find('arp')
    r = arp()
    r.opcode = r.REPLY
    r.hwdst = arpp.hwsrc
    r.protodst = arpp.protosrc
    r.hwsrc = mac
    r.protosrc = IPAddr(arpp.protodst)
    e = ethernet(type=ethernet.ARP_TYPE, src=src_mac, dst=r.hwdst)
    e.payload = r
    msg = of.ofp_packet_out()
    msg.data = e.pack()
    msg.actions.append(of.ofp_action_output(port=reply_to.port))
    msg.in_port = of.OFPP_NONE
    reply_to.connection.send(msg)


def send_arp_request(connection, ip, port=of.OFPP_FLOOD,
                     src_mac=False, src_ip=None):
    """
    Send an ARP request

    src_mac can be an EthAddr, or one of the following special values:
      False - use the "DPID MAC" (MAC based on switch DPID) -- default
      True  - use the MAC of the port the event was received by
    """
    if src_mac is False:
        src_mac = connection.eth_addr
    elif src_mac is True:
        if port in (of.OFPP_FLOOD, of.OFPP_ALL):
            for p in list(connection.ports.values()):
                if p.config & OFPPC_NO_FLOOD:
                    if port == of.ofPP_FLOOD:
                        continue
                if p.port_no < 0: continue
                if p.port_no > of.OFPP_MAX: continue  # Off by one?
                send_arp_request(connection, ip, p.port_no,
                                 src_mac=p.hw_addr, src_ip=src_ip)
            return
        src_mac = connection.ports[port].hw_addr
    else:
        src_mac = EthAddr(src_mac)
    r = arp()
    r.opcode = r.REQUEST
    r.hwdst = ETHER_BROADCAST
    r.protodst = IPAddr(ip)
    r.hwsrc = src_mac
    r.protosrc = IPAddr("0.0.0.0") if src_ip is None else IPAddr(src_ip)
    e = ethernet(type=ethernet.ARP_TYPE, src=src_mac, dst=r.hwdst)
    e.payload = r
    msg = of.ofp_packet_out()
    msg.data = e.pack()
    msg.actions.append(of.ofp_action_output(port=port))
    msg.in_port = of.OFPP_NONE
    connection.send(msg)

#classe permettant d'envoyer un paquet ARP
class ARPRequest(Event):
    @property
    def dpid(self):
        return self.connection.dpid

    def __str__(self):
        return "ARPRequest for %s on %s" % (self.ip, dpid_to_str(self.dpid))

    def __init__(self, con, arpp, reply_from, eat_packet, port, the_asker):
        super(ARPRequest, self).__init__()

        # J'ai modifier le constructeur de cette classe en augmentant the_asker,
        # qui est en fait l'adresse ip demandeuse !!!!
        self.connection = con
        self.request = arpp  # ARP packet
        self.reply_from = reply_from  # MAC or special value from send_arp_request.
        # Don't modify to use ARPHelper default.
        self.eat_packet = eat_packet
        self.port = port
        self.ip_to_mac = {"10.0.0.2": "00:00:00:00:00:11", "10.0.0.3": "00:00:00:00:00:12",
                          "90.0.0.4": "00:00:00:00:00:13", "90.0.0.5": "00:00:00:00:00:14",
                          "80.0.0.6": "00:00:00:00:00:15", "40.0.0.7": "00:00:00:00:00:16",
                          "20.0.0.8": "00:00:00:00:00:17", "10.0.0.1": "00:00:00:00:00:01",
                          "20.0.0.1": "00:00:00:00:00:02", "30.0.0.1": "00:00:00:00:00:03",
                          "40.0.0.1": "00:00:00:00:00:04", "50.0.0.1": "00:00:00:00:00:05",
                          "60.0.0.1": "00:00:00:00:00:06", "70.0.0.1": "00:00:00:00:00:07",
                          "80.0.0.1": "00:00:00:00:00:08", "90.0.0.1": "00:00:00:00:00:09"}

        self.ip = arpp.protosrc
        # Je cherche l'adresse mac voulue
        k = 0
        for key in self.ip_to_mac.keys():
            if key == the_asker:
                k = self.ip_to_mac[key]
        self.reply = k  # Set to desired EthAddr

#classe permettant d'envoyer un paquet ARP reply
class ARPReply(Event):
    @property
    def dpid(self):
        return self.connection.dpid

    def __str__(self):
        return "ARPReply for %s on %s" % (self.reply.protodst,
                                          dpid_to_str(self.dpid))

    def __init__(self, con, arpp, eat_packet, port):
        super(ARPReply, self).__init__()
        self.connection = con
        self.reply = arpp
        self.eat_packet = eat_packet
        self.port = port


_default_mac = object()

class ARPHelper(EventMixin):
    _eventMixin_events = set([ARPRequest, ARPReply])
    _rule_priority_adjustment = -0x1000  # lower than the default

    def __init__(self, no_flow, eat_packets, default_request_src_mac=False,
                 default_reply_src_mac=None, the_asker=None):
        """
        Initialize

        default_request_src_mac and default_reply_src_mac are the default source
        MAC addresses for send_arp_request() and send_arp_reply().
        """
        core.addListeners(self)
        self._install_flow = not no_flow
        self.eat_packets = eat_packets
        self.default_request_src_mac = default_request_src_mac
        self.default_reply_src_mac = default_reply_src_mac

    def send_arp_request(self, connection, ip, port=of.OFPP_FLOOD,
                         src_mac=_default_mac, src_ip=None):
        if src_mac is _default_mac:
            src_mac = self.default_request_src_mac
        return send_arp_request(connection, ip, port, src_mac, src_ip)

    def send_arp_reply(self, reply_to, mac, src_mac=_default_mac):
        """
        Send an ARP reply

        reply_to is a an ARP request PacketIn event

        mac is the MAC address to reply with, True for the port MAC or False
        for the "DPID MAC".

        src_mac can be a MAC, True/False as above, None to use "mac", or if
        unspecified, defaults to self.default_src_mac.
        """
        if src_mac is _default_mac:
            src_mac = self.default_reply_src_mac
        return send_arp_reply(reply_to, mac, src_mac)

    def _handle_GoingUpEvent(self, event):
        core.openflow.addListeners(self)

    def _handle_ConnectionUp(self, event):
        if self._install_flow:
            fm = of.ofp_flow_mod()
            fm.priority += self._rule_priority_adjustment
            fm.match.dl_type = ethernet.ARP_TYPE
            fm.actions.append(of.ofp_action_output(port=of.OFPP_CONTROLLER))
            event.connection.send(fm)

    def _handle_PacketIn(self, event):
        dpid = event.connection.dpid
        inport = event.port
        packet = event.parsed
        a = packet.find('arp')
        if not a: return
        if a.prototype != arp.PROTO_TYPE_IP:
            return
        if a.hwtype != arp.HW_TYPE_ETHERNET:
            return
        ## JE N'UTILISE QUE LA PARTIE ARP REQUEST,IE QUAND UNE STATION FAIT UNE REQUETTE,
        if a.opcode == arp.REQUEST:
            src_mac = _default_mac
            the_asker = a.protodst
            ev = ARPRequest(event.connection, a, src_mac,self.eat_packets, inport, the_asker)
            self.raiseEvent(ev)
            if ev.reply is not None:
                self.send_arp_reply(event, ev.reply, ev.reply_from)
            return EventHalt if ev.eat_packet else None
        #   JE N'UTILISE PAS CECI, C'EST PAS UTILE
        elif a.opcode == arp.REPLY:
            ev = ARPReply(event.connection, a, self.eat_packets, inport)
            self.raiseEvent(ev)
            return EventHalt if ev.eat_packet else None
        return EventHalt if self.eat_packets else None

def dpid_to_mac (dpid):
	return EthAddr("%012x" % (dpid & 0xffFFffFFffFF,))


#classe permetant de generer la liste de chemin et le chemin optimale entre deux station donnée
class L3Routing(object):
    def __init__(self, connection):
        #variable pour stocker le port qui relie l'ap a sa station
        self.ip_to_switch_port = dict({
            '10.0.0.2': ["ap1", 1],
            '10.0.0.3': ["ap1", 2],
            '90.0.0.4': ["ap9", 1],
            '90.0.0.5': ["ap9", 2],
            '80.0.0.6': ["ap8", 1],
            '40.0.0.7': ["ap4", 1],
            '20.0.0.8': ["ap2", 1]
        })
        # variable pour stocker les stations liées à leur aps
        self.switch_ips = dict({
            "ap1": ['10.0.0.2', '10.0.0.3'],
            "ap2": ['20.0.0.8'],
            "ap3": [],
            "ap4": ['40,0.0.7'],
            "ap5": [],
            "ap6": [],
            "ap7": [],
            "ap8": ['80.0.0.6'],
            "ap9": ['90.0.0.4', '90.0.0.5'],
            "apa": []
        })
        self.connection = connection
        # Adjacency list of switches
        self.switches = switches
        # List of ports connecting other switches for each switch
        self.switches_ports = switches_ports
        connection.addListeners(self)
        core.openflow_discovery.addListenerByName("LinkEvent", self._handle_LinkEvent)  # listen to openflow_discovery
        self.dst_port = {
            "00:00:00:00:00:01": ["20.0.0.0/8", 5, "90.0.0.0/8", 6, "80.0.0.0/8", 6, "40.0.0.0/8", 6, "10.0.0.0/8", 1],
            "00:00:00:00:00:02": ["20.0.0.0/8", 1, "90.0.0.0/8", 6, "80.0.0.0/8", 6, "40.0.0.0/8", 6, "10.0.0.0/8", 5],
            "00:00:00:00:00:03": ["20.0.0.0/8", 6, "90.0.0.0/8", 8, "80.0.0.0/8", 8, "40.0.0.0/8", 8, "10.0.0.0/8", 5],
            "00:00:00:00:00:04": ["20.0.0.0/8", 5, "90.0.0.0/8", 7, "80.0.0.0/8", 7, "40.0.0.0/8", 1, "10.0.0.0/8", 5],
            "00:00:00:00:00:07": ["20.0.0.0/8", 5, "90.0.0.0/8", 7, "80.0.0.0/8", 7, "40.0.0.0/8", 5, "10.0.0.0/8", 5],
            "00:00:00:00:00:09": ["20.0.0.0/8", 5, "90.0.0.0/8", 1, "80.0.0.0/8", 6, "40.0.0.0/8", 5, "10.0.0.0/8", 5],
            "00:00:00:00:00:08": ["20.0.0.0/8", 6, "90.0.0.0/8", 6, "80.0.0.0/8", 1, "40.0.0.0/8", 6, "10.0.0.0/8", 6]}
        self.my_net = 0
        self.ip_to_mac = {"10.0.0.2": "00:00:00:00:00:11", "10.0.0.3": "00:00:00:00:00:12",
                          "90.0.0.4": "00:00:00:00:00:13", "90.0.0.5": "00:00:00:00:00:14",
                          "80.0.0.6": "00:00:00:00:00:15", "40.0.0.7": "00:00:00:00:00:16",
                          "20.0.0.8": "00:00:00:00:00:17", "10.0.0.1": "00:00:00:00:00:01",
                          "20.0.0.1": "00:00:00:00:00:02", "30.0.0.1": "00:00:00:00:00:03",
                          "40.0.0.1": "00:00:00:00:00:04", "50.0.0.1": "00:00:00:00:00:05",
                          "60.0.0.1": "00:00:00:00:00:06", "70.0.0.1": "00:00:00:00:00:07",
                          "80.0.0.1": "00:00:00:00:00:08", "90.0.0.1": "00:00:00:00:00:09"}

    def _handle_LinkEvent(self, event):
        """
        Listen to link events between our network components. Specifically
        interested in links between switches at the moment. Each time such
        event occurs we pass arguments in a threaded function to run async
        Args:
            event: LinkEvent listening to openflow.discovery
        Returns: Nothing at the moment, saves topology graph and spanning tree
        """
        log.info('link detected: %s.%s -> %s.%s', "ap"+dpid_to_str( event.link.dpid1)[16],
                 event.link.port1,"ap"+dpid_to_str(event.link.dpid2)[16], event.link.port2 )
        log.debug("=================================================================")
        add_in_switches(event.link.dpid1, event.link.port1, event.link.dpid2, event.link.port2)
        add_in_switches_ports(event.link.dpid1, event.link.port1, event.link.dpid2, event.link.port2)
        add_in_switches_dpid(event.link.dpid1, event.link.dpid2)
        log.info(switches)

    def FlowMode(self, packet_in, out_port, src, dst, mac_dst):

        msg = of.ofp_flow_mod()
        msg.match.nw_dst = dst
        msg.match.nw_src = src
        msg.match.in_port = packet_in.in_port
        msg.idle_timeout = 240
        msg.match.dl_dst = mac_dst
        msg.buffer_id = packet_in.buffer_id
        msg.actions.append(of.ofp_action_output(port=out_port))
        self.connection.send(msg)
        # print(f"le msg est.... {msg}")
        log.debug("Flow install  Successfully !")

    def my_router(self, packet, packet_in, my_dpid):
        ## pour la partie Arp, j'ai décidé d'utiliser ARP_HELPER présent dans /pox/proto.. biensur, j'ai fait quelques modifications.
        #je prends la dpid de l'ap
        self.my_dpid = my_dpid
        #je met le net a 0
        self.my_net = 0
        #je convertit le dpid en mac de l'ap
        self.my_mac = dpid_to_mac(self.my_dpid)
        #je recupere le paquet de type ip
        ip_packet = packet.payload
        #je recupere l'ip source du paquet
        src_ip = ip_packet.srcip
        #je recupere l'ip de destination
        dst_ip = ip_packet.dstip
        #je met le port a zero
        port1 = 0
        log.debug( " Destination IP address : ", dst_ip )
        for key in self.dst_port.keys():
            if key == self.my_mac:
                ml = self.dst_port[key]
                for i in range(0, 10, 2):
                    mk = ml[i]
                    if dst_ip.in_network(mk):
                        port1 = ml[i + 1]
                        break
                    else:
                        continue
        k = 0
        for key in self.ip_to_mac.keys():
            if dst_ip == key:
                k = key
                break
            else:
                continue
        if k != 0:
            dsteth = EthAddr(self.ip_to_mac[k])
            msg = of.ofp_packet_out()
            action = of.ofp_action_output(port=port1)
            packet.src = packet.dst
            packet.dst = dsteth
            msg.data = packet.pack()
            msg.actions.append(action)
            self.connection.send(msg)
            self.FlowMode(packet_in, port1, src_ip, dst_ip, dsteth)

    def paths_port(self, min_path):
        stack = []
        prec = 0;
        for elt in min_path:
            if min_path[0] == elt:
                prec = elt
                continue
            stack.append(str(prec) + ' ' + str(switches_ports[prec][elt]))
            prec = elt
        stack.append(str(prec))
        return stack

    def dfs_paths(self, graph, start, goal):
        stack = [(start, [start])]
        while stack:
            (vertex, path) = stack.pop()
            for next in graph[vertex] - set(path):
                if next == goal:
                    yield path + [next]
                else:
                    stack.append((next, path + [next]))

    def install_flow_path(self, path, src_ip, dst_ip, packet):
        """"
        Cette Fonction permet d'installer les flux de donnees dans la table de flux du point d'accès
        """
        # Path length always >= 2
        prev = path[0]  # First hop
        for switch in path[1:(len(path))]:  # Dont need to install rule to the last switch in the path
            log.debug("Flow from %s to %s", prev, switch)
            msg = of.ofp_flow_mod()
            msg.idle_timeout = IDLE_TIMEOUT
            msg.hard_timeout = HARD_TIMEOUT
            msg.match.dl_type = IP_TYPE
            msg.match.nw_src = IPAddr(src_ip)
            msg.match.nw_dst = IPAddr(dst_ip)
            # msg.data = event.ofp
            output_port = self.switches_ports[prev][switch]
            msg.actions.append(of.ofp_action_output(port=output_port))
            core.openflow.getConnection(switches_dpids[prev]).send(msg)
            msg.match.dl_type = ARP_TYPE
            core.openflow.getConnection(switches_dpids[prev]).send(msg)
            log.debug("At %s rule for %s -> %s installed", prev, src_ip, dst_ip)
            log.debug("At %s output port %s to  %s", prev, output_port, switch)
            prev = switch

    def _handle_PacketIn(self, event):
        """
             Cette fonction gère le paquet envoyé par l'ap
        """
        log.debug("New packet from %s", 'ap' + dpid_to_str(self.connection.dpid)[16])
        packet = event.parsed  # This is the parsed packet data.
        packet_in = event.ofp
        self.my_dpid = event.dpid
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return
        if packet.type == packet.ARP_TYPE:
            #variable pour stocker l'adresse ip source si le paquet est de type ARP
            src_ip = str(packet.payload.protosrc)
            #variable pour stocker l'adresse ip de destination si la paquet est de type ARP
            dst_ip = str(packet.payload.protodst)
            log.debug("New ARP packet %s -> %s", src_ip, dst_ip)
        elif packet.type == packet.IP_TYPE:
            #variable pour stocker l'adresse ip source ssi le paquet est de type IP
            src_ip = str(packet.next.srcip)
            #variable pour stocker l'adresse ip de destination si le paquet est de type IP
            dst_ip = str(packet.next.dstip)
            log.debug("New IP packet %s -> %s", src_ip, dst_ip)
        else:
            log.debug("Ignoring packet type %s", packet.type)
            return
        #variable pour stocker l'ap source de l'adresse ip source
        src_switch = self.ip_to_switch_port[src_ip][0]
        #variable pour stocker l'ap de destination de l'adresse ip de destination
        dst_switch = self.ip_to_switch_port[dst_ip][0]
        log.debug("Generating paths from ap %s to %s", src_switch, dst_switch)
        paths = list(self.dfs_paths(self.switches, src_switch, dst_switch))
        log.debug("Possible paths: %s", paths)
        if ((len(paths) - 1) < 0):
            log.debug("No path between aps %s -> %s found", src_switch, dst_switch)
            return
        else:
            path = get_min_path(paths)
        log.debug("Optimal Path is : %s", path)
        log.debug("Choosen path %s", path)
        reverse_path = path[::-1]
        # Install flow rules in the switches for both directions of the connection
        log.debug("Installing rule for the reverse path %s", reverse_path)
        self.install_flow_path(reverse_path, dst_ip, src_ip, packet)
        log.debug("Installing rule for path %s", path)
        self.install_flow_path(path, src_ip, dst_ip, packet)
        list_3 = get_min_path(list(self.dfs_paths(switches, src_switch, dst_switch)))
        self.my_router(packet, packet_in, self.my_dpid)


def launch(no_flow=False, eat_packets=True, use_port_mac=False,reply_from_dst=False):
    """"
    Cette permet de charger et de lancer l'execution du programme dans la console de POX
    """
    pox.openflow.discovery.launch()
    def start_switch(event):
        log.debug("Controlling %s" % ("ap"+dpid_to_str( event.connection.dpid)[16] ,))
        L3Routing(event.connection)
    core.openflow.addListenerByName("ConnectionUp", start_switch)
    """
        Start an ARP helper

        If use_port_mac, use the specific port's MAC instead of the "DPID MAC".
        If reply_from_dst, then replies will appear to come from the MAC address
        that is used in the reply (otherwise, it comes from the same place as
        requests).
        """
    use_port_mac = str_to_bool(use_port_mac)
    reply_from_dst = str_to_bool(reply_from_dst)
    request_src = True if use_port_mac else False
    reply_src = None if reply_from_dst else request_src
    core.registerNew(ARPHelper, str_to_bool(no_flow), str_to_bool(eat_packets),request_src, reply_src)