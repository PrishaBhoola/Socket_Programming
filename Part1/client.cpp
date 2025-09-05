// CORRECTED client.cpp - Implements complete file download through chunked requests
#include <iostream>
#include <fstream>
#include <string>
#include <chrono>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <sstream>
#include <iomanip>

class WordClient {
private:
    std::string server_ip;
    int server_port;
    int k; // chunk size (words per request)
    std::string config_file;
    bool quiet_mode;
    int total_words; // Total words in file (determined dynamically)

public:
    WordClient() : config_file("config.json"), quiet_mode(false),
                  server_ip("10.0.0.2"), server_port(5000), k(5), total_words(0) {}

    bool parseArgs(int argc, char* argv[]) {
        for (int i = 1; i < argc; i++) {
            std::string arg = argv[i];
            if (arg == "--config" && i + 1 < argc) {
                config_file = argv[++i];
            } else if (arg == "--quiet") {
                quiet_mode = true;
            } else if (arg == "--k" && i + 1 < argc) {
                k = std::stoi(argv[++i]);
            }
        }
        return true;
    }

    bool get_quiet_mode() { return quiet_mode; }

    bool loadConfig() {
        std::ifstream config_file_stream(config_file);
        if (!config_file_stream.is_open()) {
            if (!quiet_mode) {
                std::cerr << "Error: Cannot open " << config_file << std::endl;
            }
            return false;
        }

        std::string line;
        while (std::getline(config_file_stream, line)) {
            if (line.find("server_ip") != std::string::npos) {
                size_t start = line.find(":") + 1;
                size_t first_quote = line.find('"', start);
                size_t second_quote = line.find('"', first_quote + 1);
                if (first_quote != std::string::npos && second_quote != std::string::npos) {
                    server_ip = line.substr(first_quote + 1, second_quote - first_quote - 1);
                }
            } else if (line.find("server_port") != std::string::npos) {
                size_t start = line.find(":") + 1;
                std::string port_str = line.substr(start);
                std::string clean_port;
                for (char c : port_str) {
                    if (isdigit(c)) clean_port += c;
                }
                if (!clean_port.empty()) {
                    server_port = std::stoi(clean_port);
                }
            } else if (line.find("\"k\"") != std::string::npos) {
                size_t start = line.find(":") + 1;
                std::string k_str = line.substr(start);
                std::string clean_k;
                for (char c : k_str) {
                    if (isdigit(c)) clean_k += c;
                }
                if (!clean_k.empty()) {
                    k = std::stoi(clean_k);
                }
            }
        }

        if (!quiet_mode) {
            std::cout << "Config loaded: " << server_ip << ":" << server_port << std::endl;
            std::cout << "Chunk size: k=" << k << std::endl;
        }
        return true;
    }

    // Get total word count from server
    int getTotalWordCount() {
        int client_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (client_fd < 0) return -1;

        // Set TCP_NODELAY
        int nodelay = 1;
        setsockopt(client_fd, IPPROTO_TCP, TCP_NODELAY, &nodelay, sizeof(nodelay));

        struct sockaddr_in server_addr{};
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(server_port);
        server_addr.sin_addr.s_addr = inet_addr("10.0.0.2");

        if (connect(client_fd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            close(client_fd);
            return -1;
        }

        // Send special SIZE request
        std::string request = "SIZE\n";
        send(client_fd, request.c_str(), request.length(), 0);

        char buffer[1024];
        memset(buffer, 0, sizeof(buffer));
        int bytes_received = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
        close(client_fd);

        if (bytes_received > 0) {
            std::string response(buffer);
            size_t pos = response.find("TOTAL:");
            if (pos != std::string::npos) {
                return std::stoi(response.substr(pos + 6));
            }
        }
        return -1;
    }

    // Make a single request for chunk starting at offset p
    std::string makeChunkRequest(int p, int chunk_k) {
        int client_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (client_fd < 0) return "";

        // Set TCP_NODELAY for immediate transmission
        int nodelay = 1;
        setsockopt(client_fd, IPPROTO_TCP, TCP_NODELAY, &nodelay, sizeof(nodelay));

        struct sockaddr_in server_addr{};
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(server_port);
        server_addr.sin_addr.s_addr = inet_addr("10.0.0.2");

        if (connect(client_fd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            close(client_fd);
            return "";
        }

        // Send request: "p,k\n"
        std::string request = std::to_string(p) + "," + std::to_string(chunk_k) + "\n";
        if (send(client_fd, request.c_str(), request.length(), 0) < 0) {
            close(client_fd);
            return "";
        }

        // Receive response
        char buffer[4096];
        memset(buffer, 0, sizeof(buffer));
        int bytes_received = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
        close(client_fd);

        if (bytes_received > 0) {
            return std::string(buffer);
        }
        return "";
    }

    // Download complete file using chunked requests
    bool downloadCompleteFile() {
        // First, get total word count
        total_words = getTotalWordCount();
        if (total_words <= 0) {
            if (!quiet_mode) {
                std::cerr << "Error: Could not determine file size" << std::endl;
            }
            return false;
        }

        if (!quiet_mode) {
            std::cout << "File contains " << total_words << " words" << std::endl;
            std::cout << "Downloading with chunk size k=" << k << std::endl;
        }

        int downloaded_words = 0;
        int current_offset = 0;
        int request_count = 0;
        std::string complete_file;

        while (downloaded_words < total_words) {
            request_count++;

            // Calculate chunk size for this request
            int remaining_words = total_words - downloaded_words;
            int chunk_size = std::min(k, remaining_words);

            if (!quiet_mode) {
                std::cout << "Request " << request_count << ": offset=" << current_offset 
                         << ", requesting " << chunk_size << " words" << std::endl;
            }

            // Make request for this chunk
            std::string response = makeChunkRequest(current_offset, chunk_size);
            if (response.empty()) {
                if (!quiet_mode) {
                    std::cerr << "Error: Request failed at offset " << current_offset << std::endl;
                }
                return false;
            }

            // Process response - count words received
            response.erase(response.find_last_not_of("\n\r") + 1);
            std::stringstream ss(response);
            std::string word;
            int words_in_chunk = 0;

            while (std::getline(ss, word, ',')) {
                word.erase(0, word.find_first_not_of(" \t"));
                word.erase(word.find_last_not_of(" \t") + 1);
                if (word == "EOF") break;
                if (!word.empty()) {
                    words_in_chunk++;
                    if (!complete_file.empty()) complete_file += ",";
                    complete_file += word;
                }
            }

            downloaded_words += words_in_chunk;
            current_offset += words_in_chunk;

            if (!quiet_mode) {
                std::cout << "Received " << words_in_chunk << " words. Progress: " 
                         << downloaded_words << "/" << total_words << std::endl;
            }

            // Check if we got EOF or fewer words than requested
            if (response.find("EOF") != std::string::npos || words_in_chunk < chunk_size) {
                break;
            }
        }

        if (!quiet_mode) {
            std::cout << "Download complete: " << downloaded_words << " words in " 
                     << request_count << " requests" << std::endl;
            std::cout << "Average words per request: " 
                     << (double)downloaded_words / request_count << std::endl;
        }

        return downloaded_words > 0;
    }

    // Run complete file download with timing
    double runWithTiming() {
        auto start = std::chrono::high_resolution_clock::now();
        bool success = downloadCompleteFile();
        auto end = std::chrono::high_resolution_clock::now();

        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        double completion_time = duration.count() / 1000.0; // Convert μs to ms

        if (success) {
            if (quiet_mode) {
                // Output format expected by run_experiments.py
                std::cout << "ELAPSED_MS:" << std::fixed << std::setprecision(3) 
                         << completion_time << std::endl;
            } else {
                std::cout << "\nTotal completion time: " << std::fixed << std::setprecision(3)
                         << completion_time << " ms" << std::endl;
            }
        }
        return success ? completion_time : -1.0;
    }
};

int main(int argc, char* argv[]) {
    WordClient client;

    if (!client.parseArgs(argc, argv)) {
        std::cerr << "Error parsing arguments" << std::endl;
        return 1;
    }

    if (!client.get_quiet_mode()) {
        std::cout << "Starting chunked file download client..." << std::endl;
    }

    if (!client.loadConfig()) {
        std::cerr << "Failed to load configuration" << std::endl;
        return 1;
    }

    double completion_time = client.runWithTiming();
    if (completion_time > 0) {
        if (!client.get_quiet_mode()) {
            std::cout << "\nFile download completed successfully!" << std::endl;
        }
        return 0;
    } else {
        if (!client.get_quiet_mode()) {
            std::cerr << "File download failed!" << std::endl;
        }
        return 1;
    }
}