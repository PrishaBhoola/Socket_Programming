#!/usr/bin/env python3
"""
FCFS Asynchronous Client for Greedy Client Fairness Analysis (Part 3)
- FINAL CORRECTED VERSION
- This version uses a single, persistent TCP connection and robust buffering.
- A greedy client sends a true "burst" of 'c' requests back-to-back before
  waiting to receive the corresponding 'c' responses. This correctly
  simulates pipelining and monopolizing the server's FCFS queue.
"""

import socket
import json
import sys
import time
import argparse
from typing import Optional

class FCFSClient:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.server_ip = self.config.get('server_ip', '10.0.0.100')
        self.server_port = self.config.get('port', 8887)
        self.k = self.config.get('k', 5)
        self.is_greedy = False
        self.c = self.config.get('c', 1)
        self.client_id = "client"
        self.quiet = False
        self.total_words = 0
        self.words_downloaded = 0
        self.sock: Optional[socket.socket] = None
        # Buffer for handling partial network receives
        self.pending_data = b""

    def load_config(self, config_file: str) -> dict:
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            if not self.quiet:
                print(f"[{self.client_id}] CONFIG ERROR: {e}", file=sys.stderr)
            return {}

    def setup_behavior(self, client_id: str, is_greedy: bool, c: int, quiet: bool):
        self.client_id = client_id
        self.is_greedy = is_greedy
        self.quiet = quiet
        if is_greedy and c:
            self.c = c

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(60.0)
            self.sock.connect((self.server_ip, self.server_port))
        except Exception as e:
            if not self.quiet:
                print(f"[{self.client_id}] ERROR: Connection failed: {e}", file=sys.stderr)
            self.sock = None

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def _receive_one_response(self) -> Optional[str]:
        """
        Waits for one complete, newline-terminated response, using an
        internal buffer to handle multiple responses arriving in one packet.
        """
        if not self.sock:
            return None
        
        # Loop until a newline is found in the buffer
        while b'\n' not in self.pending_data:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    # Connection closed by server
                    return None
                self.pending_data += chunk
            except socket.timeout:
                if not self.quiet:
                    print(f"[{self.client_id}] NETWORK TIMEOUT waiting for response.", file=sys.stderr)
                return None
            except Exception as e:
                if not self.quiet:
                    print(f"[{self.client_id}] ERROR during receive: {e}", file=sys.stderr)
                return None
        
        # Extract the first complete response from the buffer
        response, self.pending_data = self.pending_data.split(b'\n', 1)
        return response.decode().strip()


    def get_total_word_count(self) -> bool:
        try:
            self.sock.sendall(b"SIZE\n")
            response = self._receive_one_response()
            if response and response.startswith("TOTAL:"):
                self.total_words = int(response.split(':')[1])
                return True
        except Exception as e:
             if not self.quiet:
                print(f"[{self.client_id}] Failed to get word count: {e}", file=sys.stderr)
        return False

    def run_download(self) -> float:
        self.connect()
        if not self.sock or not self.get_total_word_count() or self.total_words == 0:
            self.disconnect()
            return -1.0

        start_time = time.time()
        
        try:
            while self.words_downloaded < self.total_words:
                requests_to_send = self.c if self.is_greedy else 1
                
                # --- 1. SEND A BURST OF REQUESTS ---
                sent_count = 0
                for i in range(requests_to_send):
                    current_pos = self.words_downloaded + (i * self.k)
                    if current_pos >= self.total_words:
                        break 
                    request = f"{current_pos},{self.k}\n"
                    self.sock.sendall(request.encode())
                    sent_count += 1
                
                if sent_count == 0:
                    break

                # --- 2. RECEIVE THE BURST OF RESPONSES ---
                words_this_burst = 0
                for _ in range(sent_count):
                    response = self._receive_one_response()
                    if response is None:
                        raise ConnectionAbortedError("Server connection lost while receiving burst.")
                    
                    if "EOF" in response:
                        clean_response = response.replace(",EOF", "").replace("EOF", "")
                    else:
                        clean_response = response

                    words = clean_response.split(',') if clean_response else []
                    words_this_burst += len(words)

                    if "EOF" in response:
                        self.words_downloaded = self.total_words 
                        break

                if self.words_downloaded < self.total_words:
                     self.words_downloaded += words_this_burst

        except Exception as e:
            if not self.quiet:
                print(f"[{self.client_id}] FATAL ERROR during download: {e}", file=sys.stderr)
            return -1.0
        finally:
            self.disconnect()

        return (time.time() - start_time) * 1000

def main():
    parser = argparse.ArgumentParser(description="Greedy Client for FCFS Fairness Analysis")
    parser.add_argument('--client-id', required=True, help="Unique identifier for this client")
    parser.add_argument('--greedy', action='store_true', help="Enable greedy client behavior")
    parser.add_argument('--c', type=int, help="Number of requests for a greedy client's turn")
    parser.add_argument('--quiet', action='store_true', help="Suppress verbose output for scripting")
    args = parser.parse_args()

    client = FCFSClient()
    client.setup_behavior(args.client_id, args.greedy, args.c, args.quiet)
    
    completion_time = client.run_download()

    if completion_time > 0:
        if args.quiet:
            client_type = "GREEDY" if args.greedy else "NORMAL"
            print(f"ELAPSED_MS:{completion_time:.3f}:TYPE:{client_type}")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

