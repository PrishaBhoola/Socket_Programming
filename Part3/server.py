#!/usr/bin/env python3
"""
Multithreaded FCFS Server for Greedy Client Fairness Analysis (Part 3)
- Handles multiple clients concurrently using threads.
- All requests are put into a single, thread-safe queue.
- A dedicated worker thread processes requests from the queue in FCFS order.
- Added a small delay to better simulate real-world processing load.
"""

import socket
import threading
import json
import sys
import time
import queue
from typing import List, Dict

class FCFSServer:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        
        self.server_ip = self.config.get('server_ip', '10.0.0.100')
        self.port = self.config.get('port', 8887)
        self.words = self.load_words()

        self.request_queue = queue.Queue()
        
        self.running = False
        self.server_socket = None
        self.client_threads = []

    def load_config(self, config_file: str) -> dict:
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[SERVER] CONFIG ERROR: Could not load '{config_file}'. {e}")
            return {}

    def load_words(self) -> List[str]:
        filename = self.config.get('filename', 'words.txt')
        try:
            with open(filename, 'r') as f:
                words = f.read().strip().split(',')
                print(f"[SERVER] Loaded {len(words)} words from '{filename}'.")
                return words
        except Exception as e:
            print(f"[SERVER] WORD FILE ERROR: Could not load '{filename}'. {e}")
            return []

    def start(self):
        if not self.words:
            print("[SERVER] FATAL: No words to serve. Exiting.")
            return

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.server_ip, self.port))
            self.server_socket.listen(50)
            self.running = True
            print(f"[SERVER] Listening on {self.server_ip}:{self.port}")

            processor = threading.Thread(target=self.request_processor, daemon=True)
            processor.start()

            while self.running:
                try:
                    client_sock, addr = self.server_socket.accept()
                    handler = threading.Thread(target=self.handle_client, args=(client_sock, addr), daemon=True)
                    self.client_threads.append(handler)
                    handler.start()
                except OSError:
                    break
        except Exception as e:
            print(f"[SERVER] FATAL: Could not start server. {e}")
        finally:
            self.shutdown()
            
    def handle_client(self, client_sock: socket.socket, addr: tuple):
        try:
            while self.running:
                data = client_sock.recv(1024)
                if not data:
                    break 
                
                requests = data.decode().strip().split('\n')
                for request in requests:
                    if not request: continue

                    if request == "SIZE":
                        response = f"TOTAL:{len(self.words)}\n".encode()
                        client_sock.sendall(response)
                    else:
                        # Pass the request and the original client socket to the queue
                        self.request_queue.put((request, client_sock, addr))
        except (ConnectionResetError, BrokenPipeError):
             # These errors are normal when clients disconnect abruptly
             pass
        except Exception:
             # All other exceptions
             pass
        finally:
            client_sock.close()

    def request_processor(self):
        print("[SERVER] FCFS request processor is running.")
        while self.running:
            try:
                request, client_sock, addr = self.request_queue.get(timeout=1)
                
                # Small delay to simulate processing and prevent instant completion
                time.sleep(0.01) 

                try:
                    p_str, k_str = request.split(',')
                    p, k = int(p_str), int(k_str)
                    
                    response_words = []
                    if p >= 0 and p < len(self.words):
                        end = min(p + k, len(self.words))
                        response_words = self.words[p:end]
                    
                    response = ",".join(response_words)
                    
                    if p + k >= len(self.words):
                        response += ",EOF" if response else "EOF"
                    
                    client_sock.sendall((response + '\n').encode())

                except (ValueError, IndexError):
                    client_sock.sendall(b"ERROR: Invalid request format.\n")
                except (BrokenPipeError, ConnectionResetError):
                    # This happens if the client disconnects while we're processing
                    self.request_queue.task_done()
                    continue
                finally:
                    self.request_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[SERVER-PROCESSOR] An unexpected error occurred: {e}")

    def shutdown(self):
        self.running = False
        print("\n[SERVER] Shutting down...")
        if self.server_socket:
            self.server_socket.close()
        for t in self.client_threads:
            t.join(timeout=1.0)
        print("[SERVER] Server has stopped.")

def main():
    server = FCFSServer()
    try:
        server.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()

if __name__ == "__main__":
    main()

