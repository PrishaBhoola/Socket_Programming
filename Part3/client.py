#!/usr/bin/env python3
"""
Client for Greedy FCFS Fairness Analysis (Part 3)
Can behave as normal client (1 request) or greedy client (c requests)
"""

import socket
import json
import sys
import time
import argparse
from typing import Optional

class GreedyFCFSClient:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)

        # Configuration
        self.server_ip = self.config.get('server_ip', '10.0.0.100')
        self.server_port = self.config.get('port', 8887)
        self.k = self.config.get('k', 5)
        self.p = self.config.get('p', 0)

        # Client behavior settings
        self.is_greedy = False
        self.c = self.config.get('c', 1)  # Number of requests for greedy client
        self.client_id = ""
        self.quiet = False

    def load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {}

    def set_greedy(self, is_greedy: bool, c: Optional[int] = None):
        """Set client to be greedy or normal"""
        self.is_greedy = is_greedy
        if c is not None:
            self.c = c

    def set_client_id(self, client_id: str):
        """Set client identifier"""
        self.client_id = client_id

    def set_quiet(self, quiet: bool):
        """Set quiet mode"""
        self.quiet = quiet

    def connect_to_server(self) -> Optional[socket.socket]:
        """Connect to server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30.0)
            sock.connect((self.server_ip, self.server_port))

            if not self.quiet:
                behavior = "GREEDY" if self.is_greedy else "NORMAL"
                print(f"[{self.client_id}] Connected to {self.server_ip}:{self.server_port} ({behavior})")

            return sock
        except Exception as e:
            if not self.quiet:
                print(f"[{self.client_id}] Connection error: {e}")
            return None

    def send_request(self, sock: socket.socket, p: int, k: int) -> bool:
        """Send a single request to server"""
        try:
            request = f"{p},{k}\n"
            sock.send(request.encode())

            if not self.quiet:
                print(f"[{self.client_id}] Sent request: p={p}, k={k}")

            return True
        except Exception as e:
            if not self.quiet:
                print(f"[{self.client_id}] Error sending request: {e}")
            return False

    def receive_response(self, sock: socket.socket) -> Optional[str]:
        """Receive response from server"""
        try:
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                if b'\n' in response:
                    break

            return response.decode().strip()
        except Exception as e:
            if not self.quiet:
                print(f"[{self.client_id}] Error receiving response: {e}")
            return None

    def run_normal_client(self) -> float:
        """Run as normal client - send 1 request and wait for response"""
        if not self.quiet:
            print(f"[{self.client_id}] Running as NORMAL client (1 request)")

        sock = self.connect_to_server()
        if not sock:
            return -1.0

        try:
            start_time = time.time()

            # Send single request
            if not self.send_request(sock, self.p, self.k):
                return -1.0

            # Wait for response
            response = self.receive_response(sock)
            if not response:
                return -1.0

            end_time = time.time()
            completion_time = (end_time - start_time) * 1000

            if not self.quiet:
                print(f"[{self.client_id}] Received response, completed in {completion_time:.3f} ms")

            return completion_time

        finally:
            sock.close()

    def run_greedy_client(self) -> float:
        """Run as greedy client - send c requests back-to-back, then wait for all responses"""
        if not self.quiet:
            print(f"[{self.client_id}] Running as GREEDY client ({self.c} requests)")

        sock = self.connect_to_server()
        if not sock:
            return -1.0

        try:
            start_time = time.time()

            # Send c requests back-to-back (greedy behavior)
            current_p = self.p
            for i in range(self.c):
                if not self.send_request(sock, current_p, self.k):
                    return -1.0
                current_p += self.k  # Move to next chunk

            if not self.quiet:
                print(f"[{self.client_id}] Sent all {self.c} requests, waiting for responses...")

            # Receive all c responses
            responses_received = 0
            while responses_received < self.c:
                response = self.receive_response(sock)
                if not response:
                    break
                responses_received += 1

                if not self.quiet:
                    print(f"[{self.client_id}] Received response {responses_received}/{self.c}")

            end_time = time.time()
            completion_time = (end_time - start_time) * 1000

            if responses_received == self.c:
                if not self.quiet:
                    print(f"[{self.client_id}] All responses received, completed in {completion_time:.3f} ms")
                return completion_time
            else:
                if not self.quiet:
                    print(f"[{self.client_id}] Only received {responses_received}/{self.c} responses")
                return -1.0

        finally:
            sock.close()

    def run(self) -> float:
        """Run client based on greedy/normal mode"""
        if self.is_greedy:
            return self.run_greedy_client()
        else:
            return self.run_normal_client()

def main():
    parser = argparse.ArgumentParser(description='Greedy FCFS client')
    parser.add_argument('--config', default='config.json', help='Config file')
    parser.add_argument('--client-id', default='client', help='Client identifier')
    parser.add_argument('--greedy', action='store_true', help='Run as greedy client')
    parser.add_argument('--c', type=int, help='Number of requests for greedy client')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode')

    args = parser.parse_args()

    client = GreedyFCFSClient(args.config)
    client.set_client_id(args.client_id)
    client.set_quiet(args.quiet)

    if args.greedy:
        c_value = args.c if args.c else client.c
        client.set_greedy(True, c_value)

    start_time = time.time()
    completion_time = client.run()

    if completion_time > 0:
        if args.quiet:
            behavior = "GREEDY" if client.is_greedy else "NORMAL"
            requests = client.c if client.is_greedy else 1
            print(f"ELAPSED_MS:{completion_time:.3f}:TYPE:{behavior}:REQUESTS:{requests}")
        else:
            print(f"[{args.client_id}] Success! Completion time: {completion_time:.3f} ms")
        sys.exit(0)
    else:
        if not args.quiet:
            print(f"[{args.client_id}] Failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
