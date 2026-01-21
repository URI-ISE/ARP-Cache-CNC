"""
sniffer.py - TCP Packet Sniffer for G-Code
Author: luke pepin
Description: Captures TCP packets containing G-Code instructions for analysis and modification.
"""

from scapy.all import sniff, TCP

def packet_callback(packet):
    """
    Callback for each sniffed packet. Filters for TCP packets and prints payload.
    """
    if packet.haslayer(TCP):
        payload = bytes(packet[TCP].payload)
        if payload:
            print(f"[TCP] Payload: {payload}")

# Example usage:
# sniff(filter="tcp", prn=packet_callback, store=0)
