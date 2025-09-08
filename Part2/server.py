#!/usr/bin/env python3
"""
Non-blocking TCP server for Mininet concurrent file download experiments
Uses exact IP configuration from config.json without environment detection
Handles multiple clients downloading complete files through chunked requests
Processes all requests (from all clients) in FIFO order
"""

import socket
import select
import json
import sys
import time
import os
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ClientConnection:
    """Represents a connected client"""
    socket: socket.socket
    address: tuple
    client_id: str
    connect_time: float
    current_offset: int = 0
    total_downloaded: int = 0
    is_complete: bool = False
    request_buffer: bytes = b""

@dataclass 
class QueuedRequest:
    """Represents a request in the processing queue"""
    client_id: str
    client_socket: socket.socket
    p: int
    k: int
    received_time: float
    request_number: int

class WordServer:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()

        # Server configuration - use EXACT values from config
        self.server_ip = self.config.get('server_ip', '10.0.0.100')
        self.server_port = self.config.get('server_port', 5000)
        self.words_filename = self.config.get('filename', 'words.txt')

        print(f"Server configuration:")
        print(f"  IP: {self.server_ip}")
        print(f"  Port: {self.server_port}")
        print(f"  Words file: {self.words_filename}")

        # Load word data
        self.words = self.load_words()

        # Connection management
        self.clients: Dict[str, ClientConnection] = {}

        # Request processing (FIFO queue for ALL requests from ALL clients)
        self.request_queue = deque()
        self.processing_request = False
        self.total_requests_processed = 0

        # Socket setup
        self.server_socket = None

        print(f"Server initialized: {len(self.words)} words available")

    def load_config(self) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def load_words(self) -> List[str]:
        """Load words from file"""
        try:
            with open(self.words_filename, 'r') as f:
                content = f.read().strip()
                words = [word.strip() for word in content.split(',')]
                print(f"Loaded {len(words)} words from {self.words_filename}")
                return words
        except Exception as e:
            print(f"Error loading words: {e}")
            return []

    def setup_server(self):
        """Setup non-blocking server socket"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setblocking(False)

        try:
            print(f"Binding server to {self.server_ip}:{self.server_port}")
            self.server_socket.bind((self.server_ip, self.server_port))
            self.server_socket.listen(50)  # Allow many pending connections
            print(f"✅ Server listening on {self.server_ip}:{self.server_port}")
            print(f"Ready to serve {len(self.words)} words to concurrent clients")
            return True
        except OSError as e:
            if e.errno == 98:  # Address already in use
                print(f"❌ Error: Port {self.server_port} is already in use")
                print(f"Solutions:")
                print(f"  1. Kill existing server: pkill -f 'python3 server.py'")
                print(f"  2. Wait a moment and try again")
                print(f"  3. Change server_port in {self.config_file}")
                print(f"  4. Check running processes: netstat -tuln | grep {self.server_port}")
            elif e.errno == 99:  # Cannot assign requested address
                print(f"❌ Error: Cannot bind to {self.server_ip}")
                print(f"This IP address is not available on this system")
                print(f"Make sure you're running in Mininet environment")
                print(f"Or check that {self.server_ip} is correct in {self.config_file}")
            else:
                print(f"❌ Error setting up server: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error setting up server: {e}")
            return False

    def accept_new_client(self):
        """Accept new client connection"""
        try:
            client_socket, client_addr = self.server_socket.accept()
            client_socket.setblocking(False)

            # Create unique client ID from address
            client_id = f"{client_addr[0]}:{client_addr[1]}"

            client = ClientConnection(
                socket=client_socket,
                address=client_addr,
                client_id=client_id,
                connect_time=time.time()
            )

            self.clients[client_id] = client
            print(f"Client {client_id} connected")

        except socket.error as e:
            if e.errno != socket.EWOULDBLOCK:
                print(f"Error accepting connection: {e}")

    def receive_client_data(self, client_id: str, client: ClientConnection):
        """Receive and process data from client"""
        try:
            data = client.socket.recv(1024)
            if data:
                client.request_buffer += data

                # Process complete requests (ending with \n)
                while b'\n' in client.request_buffer:
                    line_end = client.request_buffer.find(b'\n')
                    request_line = client.request_buffer[:line_end].decode().strip()
                    client.request_buffer = client.request_buffer[line_end + 1:]

                    self.handle_client_request(client_id, client, request_line)
            else:
                # Client disconnected
                print(f"Client {client_id} disconnected")
                self.remove_client(client_id)

        except socket.error as e:
            if e.errno != socket.EWOULDBLOCK:
                print(f"Error receiving from client {client_id}: {e}")
                self.remove_client(client_id)

    def handle_client_request(self, client_id: str, client: ClientConnection, request: str):
        """Handle a single request from a client"""
        if request == "SIZE":
            # Handle SIZE request immediately
            response = f"TOTAL:{len(self.words)}\n"
            try:
                client.socket.send(response.encode())
                print(f"Sent SIZE response to {client_id}")
            except socket.error as e:
                print(f"Error sending SIZE response to {client_id}: {e}")
                self.remove_client(client_id)
        else:
            try:
                # Parse p,k request
                p_str, k_str = request.split(',')
                p, k = int(p_str), int(k_str)

                # Queue the request (FIFO across ALL clients)
                queued_request = QueuedRequest(
                    client_id=client_id,
                    client_socket=client.socket,
                    p=p,
                    k=k,
                    received_time=time.time(),
                    request_number=client.current_offset // k + 1
                )

                self.request_queue.append(queued_request)
                print(f"Queued request from {client_id}: p={p}, k={k} (queue length: {len(self.request_queue)})")

            except ValueError as e:
                print(f"Invalid request from {client_id}: {request}")
                try:
                    client.socket.send(b"ERROR:Invalid format\n")
                except:
                    self.remove_client(client_id)

    def process_next_request(self):
        """Process the next request from the global FIFO queue"""
        if not self.request_queue or self.processing_request:
            return

        # Get next request from queue (FIFO across ALL clients)
        request = self.request_queue.popleft()
        self.processing_request = True
        self.total_requests_processed += 1

        print(f"Processing request #{self.total_requests_processed} from {request.client_id}: p={request.p}, k={request.k}")

        # Check if client is still connected
        if request.client_id not in self.clients:
            print(f"Client {request.client_id} no longer connected, skipping request")
            self.processing_request = False
            return

        # Generate and send response
        response = self.generate_response(request.p, request.k)

        try:
            request.client_socket.send(response.encode())
            print(f"Sent response to {request.client_id} ({len(response.strip())} chars)")

            # Update client state
            client = self.clients[request.client_id]
            words_in_response = len([w for w in response.split(',') if w.strip() and w.strip() != 'EOF'])
            client.total_downloaded += words_in_response
            client.current_offset += words_in_response

            # Check if client has completed download
            if "EOF" in response or client.total_downloaded >= len(self.words):
                client.is_complete = True
                print(f"Client {request.client_id} completed download ({client.total_downloaded} words)")

        except socket.error as e:
            print(f"Error sending response to {request.client_id}: {e}")
            self.remove_client(request.client_id)

        self.processing_request = False

    def generate_response(self, p: int, k: int) -> str:
        """Generate response for word request"""
        if p < 0 or p >= len(self.words):
            return "EOF\n"

        response_words = []
        words_sent = 0

        # Send words starting from position p
        for i in range(p, min(len(self.words), p + k)):
            response_words.append(self.words[i])
            words_sent += 1

        # Add EOF if we reached end of file
        if p + words_sent >= len(self.words):
            response_words.append("EOF")

        return ",".join(response_words) + "\n"

    def remove_client(self, client_id: str):
        """Remove client connection"""
        if client_id in self.clients:
            try:
                self.clients[client_id].socket.close()
            except:
                pass
            del self.clients[client_id]
            print(f"Removed client {client_id}")

    def get_server_stats(self):
        """Get current server statistics"""
        total_clients = len(self.clients)
        completed_clients = len([c for c in self.clients.values() if c.is_complete])
        queue_length = len(self.request_queue)

        return {
            'total_clients': total_clients,
            'completed_clients': completed_clients,
            'active_clients': total_clients - completed_clients,
            'queue_length': queue_length,
            'total_requests_processed': self.total_requests_processed
        }

    def run(self):
        """Main server event loop"""
        if not self.setup_server():
            return

        print("🚀 Server running in Mininet mode...")
        print("Press Ctrl+C to stop")
        print(f"Configured to serve {len(self.words)} words with FIFO request processing")

        last_stats_time = time.time()

        try:
            while True:
                # Prepare socket lists for select()
                read_sockets = [self.server_socket]
                write_sockets = []
                error_sockets = [self.server_socket]

                # Add client sockets
                for client in self.clients.values():
                    read_sockets.append(client.socket)
                    error_sockets.append(client.socket)

                # Use select() with short timeout
                try:
                    ready_read, ready_write, ready_error = select.select(
                        read_sockets, write_sockets, error_sockets, 0.1
                    )

                    # Handle ready sockets
                    for sock in ready_read:
                        if sock == self.server_socket:
                            self.accept_new_client()
                        else:
                            # Find client for this socket
                            client_id = None
                            for cid, client in self.clients.items():
                                if client.socket == sock:
                                    client_id = cid
                                    break

                            if client_id:
                                self.receive_client_data(client_id, self.clients[client_id])

                    # Handle socket errors
                    for sock in ready_error:
                        if sock != self.server_socket:
                            client_id = None
                            for cid, client in self.clients.items():
                                if client.socket == sock:
                                    client_id = cid
                                    break
                            if client_id:
                                print(f"Socket error for client {client_id}")
                                self.remove_client(client_id)

                    # Process next request from global queue
                    self.process_next_request()

                    # Print periodic statistics
                    current_time = time.time()
                    if current_time - last_stats_time > 10.0:  # Every 10 seconds
                        stats = self.get_server_stats()
                        if stats['total_clients'] > 0:
                            print(f"📊 Stats: {stats['active_clients']} active clients, "
                                  f"{stats['completed_clients']} completed, "
                                  f"{stats['queue_length']} queued requests, "
                                  f"{stats['total_requests_processed']} total processed")
                        last_stats_time = current_time

                except select.error as e:
                    print(f"Select error: {e}")
                    break

        except KeyboardInterrupt:
            print("\n🛑 Server shutting down...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up server resources"""
        for client_id in list(self.clients.keys()):
            self.remove_client(client_id)

        if self.server_socket:
            self.server_socket.close()

        print("Server cleanup complete")

def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.json'

    print("=== MININET FILE DOWNLOAD SERVER ===")
    print(f"Using config file: {config_file}")

    server = WordServer(config_file)
    server.run()

if __name__ == "__main__":
    main()
