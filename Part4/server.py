#!/usr/bin/env python3
"""
Round-Robin Scheduling Server for Fairness Analysis (Part 4)
- FINAL CORRECTED VERSION
- This version contains a robust, thread-safe scheduling loop that
  is not susceptible to the race conditions and deadlocks of the
  previous version.
"""

import socket
import threading
import json
from pathlib import Path
import time
from collections import deque

class RoundRobinServer:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.server_ip = self.config.get('server_ip', '10.0.0.100')
        self.port = self.config.get('port', 8887)
        self.words = self.load_words()
        
        self.clients = {}  # {client_id: {socket, address, request_queue}}
        self.client_order = deque() # A deque to manage the round-robin order
        self.lock = threading.Lock()
        self.running = True
        
        print("✅ Round-Robin Server Initialized.")
        print(f"   - Listening on: {self.server_ip}:{self.port}")
        print(f"   - Words loaded: {len(self.words)}")

    def load_config(self, config_file):
        try:
            with Path(config_file).open() as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config file: {e}", file=sys.stderr)
            return {}

    def load_words(self):
        words_path = Path('words.txt')
        if not words_path.exists():
            print("ERROR: words.txt not found!", file=sys.stderr)
            return []
        with words_path.open() as f:
            return f.read().strip().split(',')

    def handle_client_connection(self, client_socket, address):
        """Handles receiving requests from a single client and queuing them."""
        client_id = f"{address[0]}:{address[1]}"
        print(f"🤝 New connection from {client_id}")
        
        with self.lock:
            self.clients[client_id] = {
                'socket': client_socket,
                'address': address,
                'request_queue': deque()
            }
            self.client_order.append(client_id)

        try:
            buffer = ""
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                
                while '\n' in buffer:
                    request_line, buffer = buffer.split('\n', 1)
                    request_line = request_line.strip()
                    
                    if not request_line:
                        continue

                    if request_line.upper() == "SIZE":
                        response = f"TOTAL:{len(self.words)}\n"
                        client_socket.sendall(response.encode('utf-8'))
                        continue
                        
                    with self.lock:
                        if client_id in self.clients:
                            self.clients[client_id]['request_queue'].append(request_line)

        except (ConnectionResetError, BrokenPipeError):
            pass # Client disconnected normally
        except Exception as e:
            print(f"Error with client {client_id}: {e}", file=sys.stderr)
        finally:
            self.remove_client(client_id)

    def remove_client(self, client_id):
        """Safely removes a client from all server state."""
        with self.lock:
            if client_id in self.clients:
                print(f"👋 Removing client {client_id}.")
                self.clients.pop(client_id, None)
                # Rebuild the deque to safely remove the client ID
                self.client_order = deque([cid for cid in self.client_order if cid != client_id])
                
    def process_requests_round_robin(self):
        """The core scheduling logic of the server. This loop is robust against deadlocks."""
        print("🚀 Round-Robin scheduler started.")
        while self.running:
            client_id_to_serve = None
            request_to_process = None
            client_socket = None

            with self.lock:
                # If there are clients, find the next one with a pending request
                if self.client_order:
                    # Rotate to the next client in line
                    self.client_order.rotate(-1)
                    client_id_to_serve = self.client_order[0]

                    # If this client is still connected and has requests, grab one
                    if client_id_to_serve in self.clients and self.clients[client_id_to_serve]['request_queue']:
                        request_to_process = self.clients[client_id_to_serve]['request_queue'].popleft()
                        client_socket = self.clients[client_id_to_serve]['socket']
                    else:
                        client_id_to_serve = None # This client has no work
            
            # Perform the I/O operation outside the lock
            if client_id_to_serve and request_to_process and client_socket:
                try:
                    p_str, k_str = request_to_process.split(',')
                    p, k = int(p_str), int(k_str)
                    
                    response_words = self.words[p:p + k]
                    response = ",".join(response_words)
                    
                    if (p + k) >= len(self.words):
                        response += ",EOF"
                    
                    response += '\n'
                    client_socket.sendall(response.encode('utf-8'))
                except (ConnectionResetError, BrokenPipeError):
                    self.remove_client(client_id_to_serve)
                except Exception:
                    pass # Malformed request, just drop it
            else:
                # If no requests were found in this cycle, sleep briefly
                time.sleep(0.01)

    def start(self):
        """Starts the server and the main processing loop."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.server_ip, self.port))
        server_socket.listen(self.config.get("num_clients", 10) + 5)
        
        print("Server is listening for incoming connections...")

        processor_thread = threading.Thread(target=self.process_requests_round_robin, daemon=True)
        processor_thread.start()

        try:
            while self.running:
                client_socket, address = server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client_connection, args=(client_socket, address), daemon=True)
                client_thread.start()
        except KeyboardInterrupt:
            self.running = False
        finally:
            print("\nShutting down server...")
            server_socket.close()

if __name__ == "__main__":
    server = RoundRobinServer()
    server.start()

