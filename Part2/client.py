import socket
import json
import sys
import time
import argparse
from typing import Optional

class WordClient:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)

        # Configuration
        self.server_ip = self.config.get('server_ip', '10.0.0.100')
        self.server_port = self.config.get('server_port', 5000)
        self.k = self.config.get('k', 10)  # Chunk size
        self.quiet = False
        self.client_id = ""

        # Download state
        self.total_words = 0
        self.downloaded_words = 0
        self.current_offset = 0
        self.complete_file = []

    def load_config(self, config_file: str) -> dict:
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {}

    def set_quiet(self, quiet: bool):
        self.quiet = quiet

    def set_client_id(self, client_id: str):
        self.client_id = client_id

    def connect_to_server(self) -> Optional[socket.socket]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30.0)  # 30 second timeout
            sock.connect((self.server_ip, self.server_port))

            if not self.quiet:
                print(f"[{self.client_id}] Connected to {self.server_ip}:{self.server_port}")

            return sock
        except Exception as e:
            if not self.quiet:
                print(f"[{self.client_id}] Connection error: {e}")
            return None

    def get_total_words(self, sock: socket.socket) -> int:
        try:
            sock.send(b"SIZE\n")

            response = self.receive_response(sock)
            if response and response.startswith("TOTAL:"):
                total = int(response.split(":")[1])
                if not self.quiet:
                    print(f"[{self.client_id}] File contains {total} words")
                return total
            else:
                if not self.quiet:
                    print(f"[{self.client_id}] Invalid SIZE response: {response}")
                return 0

        except Exception as e:
            if not self.quiet:
                print(f"[{self.client_id}] Error getting file size: {e}")
            return 0

    def receive_response(self, sock: socket.socket) -> Optional[str]:
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

    def request_chunk(self, sock: socket.socket, offset: int, chunk_size: int) -> Optional[str]:
        try:
            request = f"{offset},{chunk_size}\n"
            sock.send(request.encode())

            if not self.quiet:
                print(f"[{self.client_id}] Requested chunk: offset={offset}, size={chunk_size}")

            response = self.receive_response(sock)
            return response

        except Exception as e:
            if not self.quiet:
                print(f"[{self.client_id}] Error requesting chunk: {e}")
            return None

    def process_chunk_response(self, response: str) -> int:
        if not response:
            return 0

        words = []
        for word in response.split(','):
            word = word.strip()
            if word and word != 'EOF':
                words.append(word)

        self.complete_file.extend(words)
        words_received = len(words)
        self.downloaded_words += words_received

        eof_reached = 'EOF' in response

        if not self.quiet:
            print(f"[{self.client_id}] Received {words_received} words "
                  f"(total: {self.downloaded_words}/{self.total_words})"
                  f"{' [EOF]' if eof_reached else ''}")

        return words_received

    def download_complete_file(self) -> bool:
        sock = self.connect_to_server()
        if not sock:
            return False

        try:
            self.total_words = self.get_total_words(sock)
            if self.total_words == 0:
                return False

            self.downloaded_words = 0
            self.current_offset = 0
            self.complete_file = []

            if not self.quiet:
                print(f"[{self.client_id}] Starting download with chunk size {self.k}")

            while self.downloaded_words < self.total_words:
                response = self.request_chunk(sock, self.current_offset, self.k)

                if not response:
                    if not self.quiet:
                        print(f"[{self.client_id}] No response received, aborting")
                    return False

                words_received = self.process_chunk_response(response)

                if words_received == 0:
                    if not self.quiet:
                        print(f"[{self.client_id}] No more words received, download complete")
                    break

                self.current_offset += words_received

                if 'EOF' in response:
                    if not self.quiet:
                        print(f"[{self.client_id}] Reached end of file")
                    break

            success = self.downloaded_words > 0
            if not self.quiet:
                print(f"[{self.client_id}] Download {'completed' if success else 'failed'}: "
                      f"{self.downloaded_words} words")

            return success

        except Exception as e:
            if not self.quiet:
                print(f"[{self.client_id}] Download error: {e}")
            return False
        finally:
            sock.close()

    def run_download_with_timing(self) -> float:
        if not self.quiet:
            print(f"[{self.client_id}] Starting timed download...")

        start_time = time.time()
        success = self.download_complete_file()
        end_time = time.time()

        completion_time = (end_time - start_time) * 1000  # Convert to ms

        if success:
            if self.quiet:
                print(f"ELAPSED_MS:{completion_time:.3f}")
            else:
                print(f"[{self.client_id}] Download completed in {completion_time:.3f} ms")
                print(f"[{self.client_id}] Downloaded {self.downloaded_words} words")
        else:
            if not self.quiet:
                print(f"[{self.client_id}] Download failed!")

        return completion_time if success else -1.0

def main():
    parser = argparse.ArgumentParser(description='Concurrent file download client')
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode for experiments')
    parser.add_argument('--client-id', default='client', help='Client identifier')

    args = parser.parse_args()

    client = WordClient(args.config)
    client.set_quiet(args.quiet)
    client.set_client_id(args.client_id)

    completion_time = client.run_download_with_timing()

    if completion_time > 0:
        if not args.quiet:
            print(f"[{args.client_id}] Success!")
        sys.exit(0)
    else:
        if not args.quiet:
            print(f"[{args.client_id}] Failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
