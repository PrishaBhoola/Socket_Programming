import socket
import json
import time
import sys
import os

def main():
    try:
        with open("config.json") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in config.json")
        sys.exit(1)

    HOST, PORT = config["server_ip"], config["server_port"]
    p, k = config["p"], config["k"]

    # Record start time
    start = time.time()

    try:
        # Create socket and connect to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(10)  # 10 second timeout
        client.connect((HOST, PORT))

        # Send request
        request = f"{p},{k}"
        client.sendall(request.encode())

        # Receive response
        response = client.recv(4096).decode()
        
        # Record end time
        end = time.time()
        elapsed_ms = (end - start) * 1000

        # Print results
        print(f"Client PID {os.getpid()}: Received {len(response.split(',')) if response else 0} words")
        print(f"Client PID {os.getpid()}: Completion time: {elapsed_ms:.3f} ms")
        
        # Optionally print first few words for verification
        if response and len(response) > 0:
            words = response.split(',')
            preview = ','.join(words[:min(5, len(words))])
            if len(words) > 5:
                preview += "..."
            print(f"Client PID {os.getpid()}: Preview: {preview}")

    except socket.timeout:
        print(f"Client PID {os.getpid()}: Connection timed out")
        sys.exit(1)
    except ConnectionRefusedError:
        print(f"Client PID {os.getpid()}: Could not connect to server at {HOST}:{PORT}")
        sys.exit(1)
    except Exception as e:
        print(f"Client PID {os.getpid()}: Error: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main()