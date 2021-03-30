"""
A stupid L3 switch
For each switch:
1) Keep a table that maps IP addresses to MAC addresses and switch ports.
   Stock this table using information from ARP and IP packets.
2) When you see an ARP query, try to answer it using information in the table
   from step 1.  If the info in the table is old, just flood the query.
3) Flood all other ARPs.
4) When you see an IP packet, if you know the destination port (because it's
   in the table from step 1), install a flow for it.
"""

from pox.core import core
import pox

log = core.getLogger()

from pox.lib.packet.ethernet import ethernet, ETHER_BROADCAST
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.arp import arp
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.util import str_to_bool, dpidToStr
from pox.lib.recoco import Timer

import pox.openflow.libopenflow_01 as of

from pox.lib.revent import *

import time

# Timeout for flows
FLOW_IDLE_TIMEOUT = 10

# Timeout for ARP entries
ARP_TIMEOUT = 60 * 2

# Maximum number of packet to buffer on a switch for an unknown IP
MAX_BUFFERED_PER_IP = 5

# Maximum time to hang on to a buffer for an unknown IP in seconds
MAX_BUFFER_TIME = 5


class Entry(object):
    """
    Not strictly an ARP entry.
    We use the port to determine which port to forward traffic out of.
    We use the MAC to answer ARP replies.
    We use the timeout so that if an entry is older than ARP_TIMEOUT, we
     flood the ARP request rather than try to answer it ourselves.

    on utilise le port pour l'envoi d'un message dans le traffic
    on utilise l'adresse MAC pour repondre aux adresses ARP
    on utilise le temps limite pour pour repondre rapidement aux requetes ARPs
    """

    def __init__(self, port, mac):
        # je definit le temps limite pour repondre aux messages
        self.timeout = time.time() + ARP_TIMEOUT
        #je definit le port de l'ap qui veut me parle par message
        self.port = port
        #je definit l'adresse MAC ou la position de l'ap qui veut me parler
        self.mac = mac

    def __eq__(self, other):
        if type(other) == tuple:
            return (self.port, self.mac) == other
        else:
            return (self.port, self.mac) == (other.port, other.mac)

    def __ne__(self, other):
        return not self.__eq__(other)

    def isExpired(self):
        if self.port == of.OFPP_NONE: return False
        return time.time() > self.timeout


def dpid_to_mac(dpid):
    #je convertir la cni de l'ap en adresse MAC de l'ap ( MAC )
    return EthAddr("%012x" % (dpid & 0xffFFffFFffFF,))


class l3_switch(EventMixin):
    def __init__(self, fakeways=[], arp_for_unknowns=False):
        # These are "fake gateways" -- we'll answer ARPs for them with MAC
        # of the switch they're connected to.
        #
        self.fakeways = set(fakeways)

        # If this is true and we see a packet for an unknown
        # host, we'll ARP for it.
        self.arp_for_unknowns = arp_for_unknowns

        # (dpid,IP) -> expire_time
        # We use this to keep from spamming ARPs
        self.outstanding_arps = {}

        # (dpid,IP) -> [(expire_time,buffer_id,in_port), ...]
        # These are buffers we've gotten at this datapath for this IP which
        # we can't deliver because we don't know where they go.
        self.lost_buffers = {}

        # For each switch, we map IP addresses to Entries
        self.arpTable = {}

        # This timer handles expiring stuff
        self._expire_timer = Timer(5, self._handle_expiration, recurring=True)

        self.listenTo(core)

    def _handle_expiration(self):
        # Called by a timer so that we can remove old items.
        empty = []
        for k, v in self.lost_buffers.iteritems():
            dpid, ip = k

            for item in list(v):
                expires_at, buffer_id, in_port = item
                if expires_at < time.time():
                    # This packet is old.  Tell this switch to drop it.
                    v.remove(item)
                    po = of.ofp_packet_out(buffer_id=buffer_id, in_port=in_port)
                    core.openflow.sendToDPID(dpid, po)
            if len(v) == 0: empty.append(k)

        # Remove empty buffer bins
        for k in empty:
            del self.lost_buffers[k]

    def _send_lost_buffers(self, dpid, ipaddr, macaddr, port):
        """
        We may have "lost" buffers -- packets we got but didn't know
        where to send at the time.  We may know now.  Try and see.
        """
        #je recoit une information qui peut exister ou pas dans mon lost_buffer et
        #je decide de renvoyer a l'ap ,identifié par sa cni et son numero par lequel il me contacte, qui m'a communiqué ca

        #si le couple constitue par la cni de l'ap et la cni source du paquet sont dans mon lost_buffers alors
        # je recupere la liste de leur description
        # je supprime cette liste de description de mon lost_buffers
        # j'affiche et j'enregistre que je suis entrain de renvoyer le message a l'ap qui m'a communiqué
        # j'envoie un message a l'ap en communiquant par son numero et une description
        # je precise dans mon message ce que l'ap devra faire ( envoi le message a un autre ap par un numero et ?? l'adresse mac de la cni source du paquet
        if (dpid, ipaddr) in self.lost_buffers:
            # Yup!
            bucket = self.lost_buffers[(dpid, ipaddr)]
            #monthe
            print ( " bucket ", bucket, " ", len( bucket ), " ", dpidToStr( dpid )  )
            del self.lost_buffers[(dpid, ipaddr)]
            log.debug("Sending %i buffered packets to %s from %s"
                      % (len(bucket), ipaddr, dpidToStr(dpid)))
            for _, buffer_id, in_port in bucket:
                #monthe
                print( " buffer_id ", buffer_id, " in_port", in_port )
                po = of.ofp_packet_out(buffer_id=buffer_id, in_port=in_port)
                po.actions.append(of.ofp_action_dl_addr.set_dst(macaddr))
                po.actions.append(of.ofp_action_output(port=port))
                #monthe revoir comment recuiperer une instance de la cni de l'ap et envoyé un message
                core.openflow.sendToDPID(dpid, po)

    def _handle_GoingUpEvent(self, event):
        self.listenTo(core.openflow)
        log.debug("Up...")

    def _handle_PacketIn(self, event):
        #je recupere le dpid de l'ap qui me contacte ou qui me parle
        dpid = event.connection.dpid
        #je recupere le numero de port par lequel l'ap veut me parlé
        #pour echanger des informations
        inport = event.port
        #je recupere le contenu du message envoyé par l'ap
        packet = event.parsed
        #si le contenue est vide alors je ne fait rien
        #sinon je verifie si la cni de l'ap est dans mon rertoire d'ap
        if not packet.parsed:
            log.warning("%i %i ignoring unparsed packet", dpid, inport)
            return

        #mon repertoire d'ap est la liste des cni de tous les aps
        #si le contenu du message n'est pas vide alors
        #si la cni de l'ap n'est pas dans mon repertoire d'ap alors
        #   je cree une nouvelle cni dans mon repertoire d'ap
        #sinon je connais l'ap par sa cni dans mon repertoire d'ap
        #donc je dois traiter le contenu du message en exploitant ses informations
        if dpid not in self.arpTable:
            # New switch -- create an empty table
            #je cree une nouvelle table d'information avec pour identificcation la cni pour l'ap dans mon repertoire d'aps
            self.arpTable[dpid] = {}
            #urgent
            print(" arpTable ",  self.arpTable[dpid], " ", dpid )
            #monthe
            print( "fakeways " , self.fakeways )
            #je parcours la liste de mes fausses passerelles
            for fake in self.fakeways:
                #monthe
                print( " fake ", fake )
                #je donne une passerelle identifiée par une IP a l'ap
                self.arpTable[dpid][IPAddr(fake)] = Entry(of.OFPP_NONE,dpid_to_mac(dpid))
                #monthe
                print( " passerelle de l'ap envoyée par le controleur ", self.arpTable[dpid][IPAddr(fake)] )

        #si le contenu du message est de type LLDP alors
        # sortir de l'application
        # sinon je recupere le contenu du message et je teste le type
        if packet.type == ethernet.LLDP_TYPE:
            # Ignore LLDP packets
            return

        #si le type du contenu 2 du message de l'ap est ipv4 alors( contenu 2 est le contenu en dessous du contenu du message )
        # afficher et enregister la cni de l'ap qui m'envoie le message, le numero par lequel l'ap me contacte, la cni source du paquet et la cni de destination du paquet
        if isinstance(packet.next, ipv4):
            log.debug("%i %i IP %s => %s", dpid, inport,
                      packet.next.srcip, packet.next.dstip)

            # Send any waiting packets...
            #je verifie si le contenu du paquet avait deja été traité par moi jusqu'a ce que c'est dans le registre lost_buffers
            #si oui alors je recupere la description et j'envoi un message a l'ap sur la base d'un
            #si non j'exploite la cni source du message envoiyé par l'ap
            self._send_lost_buffers(dpid, packet.next.srcip, packet.src, inport)

            # Learn or update port/MAC info
            #si le contenu 2 du message est dans la classe du contenu de la table d'information pour la cni de l'ap alors
            #   si la cni source du contenu 2 lié a la cni de l'ap dans sa table d'information est different du numero de l'ap et de l'adresse mac source du message alors
            #       je dois reapprendre la cni du contenu 2 du message
            #   le contenu 2 est nouvelle et il faut absolument
            if packet.next.srcip in self.arpTable[dpid]:
                #monthe
                print( " inport paquet_src ", self.arpTable[dpid][packet.next.srcip] )
                if self.arpTable[dpid][packet.next.srcip] != (inport, packet.src):
                    log.info("%i %i RE-learned %s", dpid, inport, packet.next.srcip)
            else:
                log.debug("%i %i learned %s", dpid, inport, str(packet.next.srcip))

            # monthe
            #ici je recupere le numero de l'ap qui me communique le message et l'adresse mac source du contenu
            #qui sont lié à la cni source du contenu 2 du message
            print(" inport paquet_src ", self.arpTable[dpid][packet.next.srcip])
            self.arpTable[dpid][packet.next.srcip] = Entry(inport, packet.src)

            # Try to forward
            #je recupere la cni de destination du contenu 2 du message
            dstaddr = packet.next.dstip
            #si la cni de destination du paquet est dans la classe du contenu de la table d'information de la cni de l'ap qui me contacte alors
            #       j'ai deja eu a traite le message don je recupere le numero par le lequel le message m'a ete communiqué et l'adresse mac de destination du message
            #       si le numero est utilisé pour acheminé le message vers moi alors
            #           j'affiche un avertissement que l'ap ne pourra pas envoyé le message vers la station de destination
            #       sinon j'installe les regles dans l'ap qui m'a envoyé le message et j'envoie un message à l'ap en precisant les actions qu'il devra faire
            #sinon
            if dstaddr in self.arpTable[dpid]:
                # We have info about what port to send it out on...
                #monthe
                print ( "port ", self.arpTable[dpid][dstaddr].port," mac", self.arpTable[dpid][dstaddr].mac  )
                prt = self.arpTable[dpid][dstaddr].port
                mac = self.arpTable[dpid][dstaddr].mac
                if prt == inport:
                    log.warning("%i %i not sending packet for %s back out of the " +
                                "input port" % (dpid, inport, str(dstaddr)))
                else:
                    log.debug("%i %i installing flow for %s => %s out port %i"
                              % (dpid, inport, packet.next.srcip, dstaddr, prt))

                    actions = []
                    actions.append(of.ofp_action_dl_addr.set_dst(mac))
                    actions.append(of.ofp_action_output(port=prt))
                    match = of.ofp_match.from_packet(packet, inport)
                    match.dl_src = None  # Wildcard source MAC

                    msg = of.ofp_flow_mod(command=of.OFPFC_ADD,
                                          idle_timeout=FLOW_IDLE_TIMEOUT,
                                          hard_timeout=of.OFP_FLOW_PERMANENT,
                                          buffer_id=event.ofp.buffer_id,
                                          actions=actions,
                                          match=of.ofp_match.from_packet(packet,
                                                                         inport))
                    event.connection.send(msg.pack())
            #si la cni de destination du contenu 2 du message n'est pas dans la table d'information alors
            #       je cree une nouvelle liste de description pour la cni de l'ap associé a la cni de destination du contenu 2 du message dans mon lost_buffers
            #       si la cni de l'ap et la cni de destination du contenu 2 du message est dans mon outstanding_arps alors
            #           je sort de la fonction
            #       sinon j'ajoute la cni de l'ap et la cni de destination du contenu du message dans outstanding_arps
            #       je prepare et cree la requete arp de type ethernet et avec pour adresse ether_broadcast, dstaddr, srcaddr
            #       j'envoi un message a l'ap en precisant ce qu'il doit faire ( envoie le message en utilisant tous les numeros associes et ecoutes la reponse en message des autres
            #sinon si je recoit le contenu 2 de type ARP alors
            #       je recupre le contenu 2 et j'exploite la cni de l'ap qui m'envoie le message, son numero, la cni source et de destination du contenu 2 du message
            #       si le prototype du contenu 2 du message est arp.PROTO_TYPE_IP et le hwtype du contenu 2 est ethernet et que a cni source du message est different de 0 alors
            #               si la cni source du message que j'ai recue est dans mon arpTable de la cni de l'ap alors
            #                   si (cni de l'ap , cni source du contenu 2 du message ) est diffent de ( numero de l'ap , adresse mac source ) alors
            #                       je dois reaprendre la cni , le numero, et la cni source du contenu 2 du message
            #               sinon je cree dans mon arpTable une nouvelle liste de description ( numore de l'ap, adresse source ethernet du message ) pour ( la cni de l'ap , la cni source du contenu 2 du message )
            #               je fais un send_lost_buffers ( dpid, protosrc, packet.src, inport ) envoyant un message a l'ap en precisant ce qu'il doit faire
            #               si l'opcode du contenu 2 du message est une requete et si la cni de destination du contenu 2 du message est dans mon arpTable associé a la cni de l'ap et si ( numero de l'ap , packet.dst ) n'est pas expiré alors
            #                       je prepare et cree une reponse arp et je precise a l'ap d'envoye le message par le port of.OFPP_IN_PORT

            elif self.arp_for_unknowns:
                # We don't know this destination.
                # First, we track this buffer so that we can try to resend it later
                # if we learn the destination, second we ARP for the destination,
                # which should ultimately result in it responding and us learning
                # where it is

                # Add to tracked buffers
                if (dpid, dstaddr) not in self.lost_buffers:
                    self.lost_buffers[(dpid, dstaddr)] = []
                bucket = self.lost_buffers[(dpid, dstaddr)]
                entry = (time.time() + MAX_BUFFER_TIME, event.ofp.buffer_id, inport)
                bucket.append(entry)
                while len(bucket) > MAX_BUFFERED_PER_IP: del bucket[0]
                #monthe
                print( " bucket dst ", bucket )

                # Expire things from our outstanding ARP list...
                self.outstanding_arps = {k: v for k, v in
                                         self.outstanding_arps.iteritems() if v > time.time()}

                # Check if we've already ARPed recently
                if (dpid, dstaddr) in self.outstanding_arps:
                    # Oop, we've already done this one recently.
                    return

                # And ARP...
                self.outstanding_arps[(dpid, dstaddr)] = time.time() + 4

                r = arp()
                r.hwtype = r.HW_TYPE_ETHERNET
                r.prototype = r.PROTO_TYPE_IP
                r.hwlen = 6
                r.protolen = r.protolen
                r.opcode = r.REQUEST
                r.hwdst = ETHER_BROADCAST
                r.protodst = dstaddr
                r.hwsrc = packet.src
                r.protosrc = packet.next.srcip
                e = ethernet(type=ethernet.ARP_TYPE, src=packet.src,
                             dst=ETHER_BROADCAST)
                e.set_payload(r)
                #monthe
                print ( " dpid ", dpid, " inport", inport," str(r.protodst)", str(r.protodst), " str(r.protosrc)", str(r.protosrc) )
                log.debug("%i %i ARPing for %s on behalf of %s" % (dpid, inport,
                                                                   str(r.protodst), str(r.protosrc)))
                msg = of.ofp_packet_out()
                msg.data = e.pack()
                msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
                msg.in_port = inport
                event.connection.send(msg)
        elif isinstance(packet.next, arp):
            a = packet.next
            log.debug("%i %i ARP %s %s => %s", dpid, inport,
                      {arp.REQUEST: "request", arp.REPLY: "reply"}.get(a.opcode,
                                                                       'op:%i' % (a.opcode,)), str(a.protosrc),
                      str(a.protodst))

            if a.prototype == arp.PROTO_TYPE_IP:
                if a.hwtype == arp.HW_TYPE_ETHERNET:
                    if a.protosrc != 0:

                        # Learn or update port/MAC info
                        if a.protosrc in self.arpTable[dpid]:
                            #monthe
                            print( " dpid", dpid, " inport",  inport, " str(a.protosrc)", str(a.protosrc) )
                            if self.arpTable[dpid][a.protosrc] != (inport, packet.src):
                                log.info("%i %i RE-learned %s", dpid, inport, str(a.protosrc))
                        else:
                            #monthe
                            print(" dpid", dpid, " inport", inport, " str(a.protosrc)", str(a.protosrc))
                            log.debug("%i %i learned %s", dpid, inport, str(a.protosrc))
                        self.arpTable[dpid][a.protosrc] = Entry(inport, packet.src)

                        # Send any waiting packets...
                        self._send_lost_buffers(dpid, a.protosrc, packet.src, inport)

                        if a.opcode == arp.REQUEST:
                            # Maybe we can answer

                            if a.protodst in self.arpTable[dpid]:
                                # We have an answer...

                                if not self.arpTable[dpid][a.protodst].isExpired():
                                    # .. and it's relatively current, so we'll reply ourselves

                                    r = arp()
                                    r.hwtype = a.hwtype
                                    r.prototype = a.prototype
                                    r.hwlen = a.hwlen
                                    r.protolen = a.protolen
                                    r.opcode = arp.REPLY
                                    r.hwdst = a.hwsrc
                                    r.protodst = a.protosrc
                                    r.protosrc = a.protodst
                                    r.hwsrc = self.arpTable[dpid][a.protodst].mac
                                    e = ethernet(type=packet.type, src=dpid_to_mac(dpid), dst=a.hwsrc)
                                    e.set_payload(r)
                                    log.debug("%i %i answering ARP for %s" % (dpid, inport,
                                                                              str(r.protosrc)))
                                    #monthe
                                    print ( "arp response dpid ", dpid,"  numero de l'ap ",  inport," str( r.protosrc ) ",
                                                                              str(r.protosrc))
                                    msg = of.ofp_packet_out()
                                    msg.data = e.pack()
                                    msg.actions.append(of.ofp_action_output(port=
                                                                            of.OFPP_IN_PORT))
                                    msg.in_port = inport
                                    event.connection.send(msg)
                                    return

            # Didn't know how to answer or otherwise handle this ARP, so just flood it
            log.debug("%i %i flooding ARP %s %s => %s" % (dpid, inport,
                                                          {arp.REQUEST: "request", arp.REPLY: "reply"}.get(a.opcode,
                                                                                                           'op:%i' % (
                                                                                                           a.opcode,)),
                                                          str(a.protosrc), str(a.protodst)))

            #monthe
            print ( " flood dpid ", dpid," in port ", inport, " a.protosrc", a.protosrc, " a.protodst ", a.protodst )
            msg = of.ofp_packet_out(in_port=inport, action=of.ofp_action_output(port=of.OFPP_FLOOD))
            if event.ofp.buffer_id is of.NO_BUFFER:
                # Try sending the (probably incomplete) raw data
                msg.data = event.data
            else:
                msg.buffer_id = event.ofp.buffer_id
            event.connection.send(msg.pack())


def launch(fakeways="", arp_for_unknowns=None):
    fakeways = fakeways.replace(",", " ").split()
    fakeways = [IPAddr(x) for x in fakeways]
    if arp_for_unknowns is None:
        arp_for_unknowns = len(fakeways) > 0
    else:
        arp_for_unknowns = str_to_bool(arp_for_unknowns)
    core.registerNew(l3_switch, fakeways, arp_for_unknowns)