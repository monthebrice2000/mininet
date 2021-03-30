To make it properly works, first get familiar with mininet and openflow framework.

After running the initial tutorial of POX as remote controller for mininet, just overwrite the file
<path_to_pox>/pox/misc/of_tutorial.py. Now the controller provided here will be the controller of your
SDN.
/** 
MONTHE
*/
placing F2 component in misc folder of POX misc/pox.py
running POX
./pox.py log.level --DEBUG  misc.F2 samples.pretty_log

/**
MONTHE
*/

placer le dossier mininet-wifi dans n'importe quel dossier mais pas dans le meme dossier qui contient votre mininet personnelle
se placer dans le dossier mininet-wifi et ouvrir le terminal depuis ce dernier
taper la commande : sudo python2 meshRemoteControlWirelessNodesInformations.py