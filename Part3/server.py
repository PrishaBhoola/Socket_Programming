#!/usr/bin/env python3
"""
FCFS Server for Greedy Client Fairness Analysis (Part 3)
Processes requests sequentially in First-Come-First-Serve order
Tracks timing and fairness metrics for analysis
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
    requests_received: int = 0
    requests_completed: int = 0
    first_request_time: Optional[float] = None
    last_response_time: Optional[float] = None

@dataclass 
class QueuedRequest:
    """Represents a request in the FCFS queue"""
    client_id: str
    client_socket: socket.socket
    p: int
    k: int
    received_time: float
    request_sequence: int  # Which request number for this client

class GreedyFCFSServer:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()

        # Server configuration
        self.server_ip = self.config.get('server_ip', '10.0.0.100')
        self.server_port = self.config.get('port', 8887)
        self.words_filename = self.config.get('filename', 'words.txt')

        # Load word data
        self.words = self.load_words()

        # Connection management
        self.clients: Dict[str, ClientConnection] = {}

        # FCFS request queue - this is the key for fairness analysis
        self.request_queue = deque()
        self.processing_request = False
        self.total_requests_processed = 0

        # Fairness tracking
        self.request_log = []  # Log of all requests for analysis

        # Socket setup
        self.server_socket = None

        print(f"Greedy FCFS Server initialized")
        print(f"Server: {self.server_ip}:{self.server_port}")
        print(f"Words available: {len(self.words)}")

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
            self.server_socket.listen(50)
            print(f"✅ Server listening on {self.server_ip}:{self.server_port}")
            print(f"Ready for FCFS greedy client analysis")
            return True
        except Exception as e:
            print(f"❌ Error setting up server: {e}")
            return False

    def accept_new_client(self):
        """Accept new client connection"""
        try:
            client_socket, client_addr = self.server_socket.accept()
            client_socket.setblocking(False)

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
                # Process request
                request_line = data.decode().strip()

                if request_line == "SIZE":
                    # Handle SIZE request immediately
                    response = f"TOTAL:{len(self.words)}\n"
                    try:
                        client.socket.send(response.encode())
                        print(f"Sent SIZE response to {client_id}")
                    except socket.error as e:
                        print(f"Error sending SIZE response: {e}")
                        self.remove_client(client_id)
                else:
                    try:
                        # Parse p,k request
                        p_str, k_str = request_line.split(',')
                        p, k = int(p_str), int(k_str)

                        # Track client request timing
                        current_time = time.time()
                        if client.first_request_time is None:
                            client.first_request_time = current_time

                        client.requests_received += 1

                        # Add to FCFS queue
                        queued_request = QueuedRequest(
                            client_id=client_id,
                            client_socket=client.socket,
                            p=p,
                            k=k,
                            received_time=current_time,
                            request_sequence=client.requests_received
                        )

                        self.request_queue.append(queued_request)

                        print(f"Queued request from {client_id} (#{client.requests_received}): p={p}, k={k}")
                        print(f"  Queue length: {len(self.request_queue)}")

                    except ValueError as e:
                        print(f"Invalid request from {client_id}: {request_line}")

            else:
                # Client disconnected
                print(f"Client {client_id} disconnected")
                self.remove_client(client_id)

        except socket.error as e:
            if e.errno != socket.EWOULDBLOCK:
                print(f"Error receiving from client {client_id}: {e}")
                self.remove_client(client_id)

    def process_next_request(self):
        """Process the next request from FCFS queue"""
        if not self.request_queue or self.processing_request:
            return

        # Get next request from FCFS queue
        request = self.request_queue.popleft()
        self.processing_request = True
        self.total_requests_processed += 1

        # Log for fairness analysis
        process_start_time = time.time()

        print(f"Processing FCFS request #{self.total_requests_processed}")
        print(f"  From: {request.client_id} (sequence #{request.request_sequence})")
        print(f"  Request: p={request.p}, k={request.k}")
        print(f"  Queue time: {(process_start_time - request.received_time)*1000:.1f} ms")

        # Check if client still connected
        if request.client_id not in self.clients:
            print(f"  Client {request.client_id} no longer connected")
            self.processing_request = False
            return

        # Generate response
        response = self.generate_response(request.p, request.k)

        try:
            # Send response
            request.client_socket.send(response.encode())
            process_end_time = time.time()

            # Update client tracking
            client = self.clients[request.client_id]
            client.requests_completed += 1
            client.last_response_time = process_end_time

            # Log for analysis
            self.request_log.append({
                'client_id': request.client_id,
                'request_sequence': request.request_sequence,
                'received_time': request.received_time,
                'process_start_time': process_start_time,
                'process_end_time': process_end_time,
                'queue_time_ms': (process_start_time - request.received_time) * 1000,
                'processing_time_ms': (process_end_time - process_start_time) * 1000
            })

            print(f"  Sent response to {request.client_id}")
            print(f"  Client completed requests: {client.requests_completed}")

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

    def get_fairness_stats(self):
        """Calculate fairness statistics"""
        stats = {
            'total_clients': len(self.clients),
            'total_requests_processed': self.total_requests_processed,
            'queue_length': len(self.request_queue),
            'clients_by_requests': {}
        }

        for client_id, client in self.clients.items():
            stats['clients_by_requests'][client_id] = {
                'requests_received': client.requests_received,
                'requests_completed': client.requests_completed,
                'connect_time': client.connect_time,
                'first_request_time': client.first_request_time,
                'last_response_time': client.last_response_time
            }

        return stats

    def run(self):
        """Main server event loop"""
        if not self.setup_server():
            return

        print("🚀 FCFS Server running for greedy client analysis...")
        print("Press Ctrl+C to stop and see fairness analysis")

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

                    # Process next request in FCFS order
                    self.process_next_request()

                    # Periodic stats
                    current_time = time.time()
                    if current_time - last_stats_time > 10.0:
                        stats = self.get_fairness_stats()
                        print(f"📊 FCFS Stats: {stats['total_clients']} clients, "
                              f"{stats['total_requests_processed']} processed, "
                              f"{stats['queue_length']} queued")
                        last_stats_time = current_time

                except select.error as e:
                    print(f"Select error: {e}")
                    break

        except KeyboardInterrupt:
            print("\n🛑 Server shutting down...")
            self.print_fairness_analysis()
        finally:
            self.cleanup()

    def print_fairness_analysis(self):
        """Print detailed fairness analysis"""
        if not self.request_log:
            print("No requests to analyze")
            return

        print("\n" + "="*60)
        print("FAIRNESS ANALYSIS")
        print("="*60)

        # Group by client
        client_requests = {}
        for req in self.request_log:
            client_id = req['client_id']
            if client_id not in client_requests:
                client_requests[client_id] = []
            client_requests[client_id].append(req)

        print(f"\nClients: {len(client_requests)}")
        print(f"Total requests processed: {len(self.request_log)}")

        print("\nPer-Client Analysis:")
        print("Client ID                | Requests | Avg Queue Time | Total Time")
        print("-" * 70)

        for client_id, requests in client_requests.items():
            avg_queue_time = sum(r['queue_time_ms'] for r in requests) / len(requests)
            first_req = min(requests, key=lambda x: x['received_time'])
            last_req = max(requests, key=lambda x: x['process_end_time'])
            total_time = (last_req['process_end_time'] - first_req['received_time']) * 1000

            print(f"{client_id:24} | {len(requests):8d} | {avg_queue_time:12.1f} ms | {total_time:8.1f} ms")

        # Identify potential greedy client
        max_requests = max(len(requests) for requests in client_requests.values())
        greedy_clients = [client_id for client_id, requests in client_requests.items() 
                         if len(requests) == max_requests and max_requests > 1]

        if greedy_clients:
            print(f"\n🎯 Potential greedy client(s): {', '.join(greedy_clients)}")
            print(f"   Sent {max_requests} requests vs 1 for others")

    def cleanup(self):
        """Clean up server resources"""
        for client_id in list(self.clients.keys()):
            self.remove_client(client_id)

        if self.server_socket:
            self.server_socket.close()

        print("Server cleanup complete")

def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    print(f"=== GREEDY CLIENT FCFS SERVER (Part 3) ===")
    print(f"Config: {config_file}")

    server = GreedyFCFSServer(config_file)
    server.run()

if __name__ == "__main__":
    main()
