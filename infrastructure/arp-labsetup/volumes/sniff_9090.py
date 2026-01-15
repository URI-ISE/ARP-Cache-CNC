from scapy.all import *
from datetime import datetime

print("Now sniffing traffic on port 9090...")

seen_seqs = set()
log_path = f"/volumes/sniffed_packets_{datetime.now().strftime('%Y-%m-%d')}.log"

def pkt_callback(pkt):
    if pkt.haslayer(IP) and pkt.haslayer(TCP) and pkt.haslayer(Raw):
        src = pkt[IP].src
        dst = pkt[IP].dst
        seq = pkt[TCP].seq
        key = (src, dst, seq)

        if key in seen_seqs:
            return  # Skip retransmissions

        seen_seqs.add(key)

        try:
            payload = pkt[Raw].load.decode(errors="ignore").strip()
        except:
            payload = "[non-printable data]"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Source IP: {src} → Destination IP: {dst} | Seq: {seq} | Payload: {payload}")
        print("-" * 40)
        log_entry = f"{timestamp},{src},{dst},{seq},{payload}"

        with open(log_path, "a") as f:
            f.write(log_entry + "\n")

sniff(iface="eth0", filter="tcp port 9090", prn=pkt_callback, store=0)
