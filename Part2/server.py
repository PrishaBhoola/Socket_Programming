import socket
import json
import threading
import time
import sys

def load_words(filename, p, k):
    """Load k words starting from position p from the file."""
    try:
        with open(filename, "r") as f:
            words = f.read().strip().split(",")
        
        # Handle bounds checking
        if p >= len(words):
            return []
        
        end_idx = min(p + k, len(words))
        return words[p:end_idx]
    except FileNotFoundError:
        print(f"Error: File {filename} not found")
        return []
    except Exception as e:
        print(f"Error loading words: {e}")
        return []

def handle_client(conn, addr, config):
    """Handle a single client connection."""
    try:
        print(f"[SERVER] Client {addr} connected")
        
        # Receive data from client
        data = conn.recv(1024).decode().strip()
        if not data:
            print(f"[SERVER] No data received from {addr}")
            return
        
        # Parse client request
        try:
            p, k = map(int, data.split(","))
        except ValueError:
            print(f"[SERVER] Invalid request format from {addr}: {data}")
            conn.sendall(b"ERROR: Invalid request format")
            return
        
        # Load requested words
        words = load_words(config["filename"], p, k)
        
        # Send response
        response = ",".join(words)
        conn.sendall(response.encode())
        
        print(f"[SERVER] Served {len(words)} words to {addr} (p={p}, k={k})")
        
    except Exception as e:
        print(f"[SERVER] Error handling client {addr}: {e}")
    finally:
        conn.close()
        print(f"[SERVER] Connection to {addr} closed")

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

    # Create and configure server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        server.listen(50)  # Allow up to 50 queued connections
        print(f"[SERVER] Listening on {HOST}:{PORT}")
        print(f"[SERVER] Ready to handle concurrent connections...")
        
        while True:
            try:
                # Accept new connection
                conn, addr = server.accept()
                
                # Handle each client in a separate thread for concurrency
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(conn, addr, config),
                    daemon=True
                )
                client_thread.start()
                
            except KeyboardInterrupt:
                print("\n[SERVER] Shutting down...")
                break
            except Exception as e:
                print(f"[SERVER] Error accepting connections: {e}")
                
    except Exception as e:
        print(f"[SERVER] Failed to start server: {e}")
        sys.exit(1)
    finally:
        server.close()
        print("[SERVER] Server closed")

if __name__ == "__main__":
    main()