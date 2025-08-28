#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <map>
#include <vector>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <chrono>

class WordClient {
private:
    std::string server_ip;
    int server_port;
    int p;  // starting offset
    int k;  // number of words to request
    std::string config_file;
    bool quiet_mode;

public:
    WordClient() : config_file("config.json"), quiet_mode(false) {}

    // Parse command line arguments
    bool parseArgs(int argc, char* argv[]) {
        for (int i = 1; i < argc; i++) {
            std::string arg = argv[i];

            if (arg == "--config" && i + 1 < argc) {
                config_file = argv[++i];
            }
            else if (arg == "--quiet") {
                quiet_mode = true;
            }
            else if (arg == "--timing") {
                // Legacy support for --timing flag
                quiet_mode = false;
            }
            else if (arg == "--k" && i + 1 < argc) {
                k = std::stoi(argv[++i]);
            }
        }
        return true;
    }
    bool get_quiet_mode(){
        return this->quiet_mode;
    }
    // Load configuration from specified config file
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
            // Simple parsing - look for key-value pairs
            if (line.find("server_ip") != std::string::npos) {
                size_t start = line.find(":") + 1;
                size_t first_quote = line.find('"', start);
                size_t second_quote = line.find('"', first_quote + 1);
                if (first_quote != std::string::npos && second_quote != std::string::npos) {
                    server_ip = line.substr(first_quote + 1, second_quote - first_quote - 1);
                }
            }
            else if (line.find("server_port") != std::string::npos) {
                size_t start = line.find(":") + 1;
                std::string port_str = line.substr(start);
                std::string clean_port;
                for (char c : port_str) {
                    if (isdigit(c)) clean_port += c;
                }
                if (!clean_port.empty()) {
                    server_port = std::stoi(clean_port);
                }
            }
            else if (line.find("\"p\"") != std::string::npos) {
                size_t start = line.find(":") + 1;
                std::string p_str = line.substr(start);
                std::string clean_p;
                for (char c : p_str) {
                    if (isdigit(c)) clean_p += c;
                }
                if (!clean_p.empty()) {
                    p = std::stoi(clean_p);
                }
            }
            else if (line.find("\"k\"") != std::string::npos) {
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
            std::cout << "Request parameters: p=" << p << ", k=" << k << std::endl;
        }
        return true;
    }

    // Count word frequencies from received words
    void countWordFrequencies(const std::string& words_response) {
        std::map<std::string, int> word_count;

        std::string clean_response = words_response;
        clean_response.erase(clean_response.find_last_not_of("\n\r") + 1);

        std::stringstream ss(clean_response);
        std::string word;

        while (std::getline(ss, word, ',')) {
            word.erase(0, word.find_first_not_of(" \t"));
            word.erase(word.find_last_not_of(" \t") + 1);

            if (word == "EOF") continue;
            if (!word.empty()) {
                word_count[word]++;
            }
        }

        if (!quiet_mode) {
            std::cout << "\nWord frequencies:" << std::endl;
            for (const auto& pair : word_count) {
                std::cout << pair.first << ", " << pair.second << std::endl;
            }
        }
    }

    // Connect to server and make request
    bool makeRequest() {
        int client_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (client_fd < 0) {
            if (!quiet_mode) {
                std::cerr << "Error: Cannot create socket" << std::endl;
            }
            return false;
        }

        struct sockaddr_in server_addr{};
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(server_port);

        if (server_ip == "localhost" || server_ip == "127.0.0.1") {
            server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
        } else {
            if (inet_pton(AF_INET, server_ip.c_str(), &server_addr.sin_addr) <= 0) {
                if (!quiet_mode) {
                    std::cerr << "Error: Invalid server IP address: " << server_ip << std::endl;
                }
                close(client_fd);
                return false;
            }
        }

        if (connect(client_fd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            if (!quiet_mode) {
                std::cerr << "Error: Connection failed" << std::endl;
            }
            close(client_fd);
            return false;
        }

        if (!quiet_mode) {
            std::cout << "Connected to server " << server_ip << ":" << server_port << std::endl;
        }

        std::string request = std::to_string(p) + "," + std::to_string(k) + "\n";
        if (!quiet_mode) {
            std::cout << "Sending request: " << request;
        }

        if (send(client_fd, request.c_str(), request.length(), 0) < 0) {
            if (!quiet_mode) {
                std::cerr << "Error: Failed to send request" << std::endl;
            }
            close(client_fd);
            return false;
        }

        char buffer[4096];
        memset(buffer, 0, sizeof(buffer));

        int bytes_received = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
        if (bytes_received < 0) {
            if (!quiet_mode) {
                std::cerr << "Error: Failed to receive response" << std::endl;
            }
            close(client_fd);
            return false;
        }
        else if (bytes_received == 0) {
            if (!quiet_mode) {
                std::cout << "Server closed connection" << std::endl;
            }
        }
        else {
            std::string response(buffer);
            if (!quiet_mode) {
                std::cout << "Received response: " << response;
            }

            // Process the response
            countWordFrequencies(response);
        }

        close(client_fd);
        if (!quiet_mode) {
            std::cout << "Connection closed" << std::endl;
        }

        return bytes_received > 0;
    }

    // Run client with timing and return completion time
    double runWithTiming() {
        auto start_time = std::chrono::high_resolution_clock::now();

        bool success = makeRequest();

        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
        double completion_time = duration.count() / 1000.0;

        if (success) {
            if (quiet_mode) {
                // Output in the format expected by run_experiments.py
                std::cout << "ELAPSED_MS:" << (int)completion_time << std::endl;
            } else {
                std::cout << "\nCompletion time: " << completion_time << " ms" << std::endl;
            }
        }

        return success ? completion_time : -1.0;
    }
};

int main(int argc, char* argv[]) {
    WordClient client;

    // Parse command line arguments
    if (!client.parseArgs(argc, argv)) {
        std::cerr << "Error parsing arguments" << std::endl;
        return 1;
    }

    if (!client.get_quiet_mode()) {
        std::cout << "Starting word counting client..." << std::endl;
    }

    // Load configuration
    if (!client.loadConfig()) {
        std::cerr << "Failed to load configuration" << std::endl;
        return 1;
    }

    // Always run with timing for the experiment
    double completion_time = client.runWithTiming();

    if (completion_time > 0) {
        if (!client.get_quiet_mode()) {
            std::cout << "\nRequest completed successfully!" << std::endl;
        }
        return 0;
    } else {
        if (!client.get_quiet_mode()) {
            std::cerr << "Request failed!" << std::endl;
        }
        return 1;
    }
}