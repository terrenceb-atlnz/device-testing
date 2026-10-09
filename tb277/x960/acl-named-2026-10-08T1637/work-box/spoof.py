import sys
from scapy.all import Ether, IP, ICMP, sendp
src = sys.argv[1]
pkts = [Ether(src=src, dst='00:00:cd:42:30:29')/IP(src='10.38.22.65', dst='10.38.22.70')/ICMP(seq=i) for i in range(5)]
sendp(pkts, iface='eth4', verbose=0)
print('sent 5 frames with source MAC', src)
