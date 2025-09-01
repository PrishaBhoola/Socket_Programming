#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>

class WordServer {
private:
    std::vector<std::string> words;
    std::string server_ip;
    int server_port;
    std::string words_filename;
    std::string config_file;

public:
    // FIXED: Initialize all member variables with defaults
    WordServer() : config_file("demo_config.json"), 
                   server_ip("10.0.0.2"), server_port(5000), 
                   words_filename("words.txt") {}

    // Parse command line arguments
    bool parseArgs(int argc, char* argv[]) {
        for (int i = 1; i < argc; i++) {
            std::string arg = argv[i];

            if (arg == "--config" && i + 1 < argc) {
                config_file = argv[++i];
            }
        }
        return true;
    }

    // Load configuration from specified config file
    bool loadConfig() {
        std::ifstream config_file_stream(config_file);
        if (!config_file_stream.is_open()) {
            std::cerr << "Error: Cannot open " << config_file << std::endl;
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
            else if (line.find("filename") != std::string::npos) {
                size_t start = line.find(":") + 1;
                size_t first_quote = line.find('"', start);
                size_t second_quote = line.find('"', first_quote + 1);
                if (first_quote != std::string::npos && second_quote != std::string::npos) {
                    words_filename = line.substr(first_quote + 1, second_quote - first_quote - 1);
                }
            }
        }

        std::cout << "Config loaded: " << server_ip << ":" << server_port << std::endl;
        std::cout << "Words file: " << words_filename << std::endl;
        return true;
    }

    // Load words from words.txt file
    bool loadWords() {
        std::ifstream words_file(words_filename);
        if (!words_file.is_open()) {
            std::cerr << "Error: Cannot open " << words_filename << std::endl;
            return false;
        }

        std::string line;
        if (std::getline(words_file, line)) {
            std::stringstream ss(line);
            std::string word;

            while (std::getline(ss, word, ',')) {
                word.erase(0, word.find_first_not_of(" \t"));
                word.erase(word.find_last_not_of(" \t") + 1);
                if (!word.empty()) words.push_back(word);
            }
        }

        std::cout << "Loaded " << words.size() << " words from " << words_filename << std::endl;
        return !words.empty();
    }

    // Handle client request and generate response
    std::string handleRequest(const std::string& request) {
        std::stringstream ss(request);
        std::string p_str, k_str;

        if (!std::getline(ss, p_str, ',') || !std::getline(ss, k_str)) {
            return "EOF\n";
        }

        // Clean up k_str (remove newlines, spaces, etc.)
        k_str.erase(k_str.find_last_not_of("\n\r \t") + 1);

        try {
            int p = std::stoi(p_str);
            int k = std::stoi(k_str);

            std::cout << "Request: p=" << p << ", k=" << k << std::endl;

            // Validate offset
            if (p < 0 || p >= (int)words.size()) {
                return "EOF\n";
            }

            std::string response;
            int words_sent = 0;

            // Add words starting from position p
            for (int i = p; i < (int)words.size() && words_sent < k; i++) {
                if (words_sent > 0) response += ",";
                response += words[i];
                words_sent++;
            }

            // Add EOF if we couldn't send k words
            if (words_sent < k) {
                if (words_sent > 0) response += ",";
                response += "EOF";
            }

            response += "\n";
            return response;

        } catch (...) {
            return "EOF\n";
        }
    }

    // Main server loop
    void run() {
        int server_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (server_fd < 0) {
            std::cerr << "Error: Cannot create socket" << std::endl;
            return;
        }

        int opt = 1;
        if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
            std::cerr << "Error: setsockopt failed" << std::endl;
            close(server_fd);
            return;
        }

        struct sockaddr_in server_addr{};
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(server_port);

        if (server_ip == "0.0.0.0" || server_ip == "localhost") {
            server_addr.sin_addr.s_addr = INADDR_ANY;
        } else {
            if (inet_pton(AF_INET, server_ip.c_str(), &server_addr.sin_addr) <= 0) {
                std::cerr << "Invalid IP. Using any interface." << std::endl;
                server_addr.sin_addr.s_addr = INADDR_ANY;
            }
        }

        if (bind(server_fd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            std::cerr << "Error: Bind failed on port " << server_port << std::endl;
            close(server_fd);
            return;
        }

        if (listen(server_fd, 5) < 0) {
            std::cerr << "Error: Listen failed" << std::endl;
            close(server_fd);
            return;
        }

        std::cout << "Server listening on port " << server_port << std::endl;

        while (true) {
            struct sockaddr_in client_addr{};
            socklen_t client_len = sizeof(client_addr);
            int client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &client_len);

            if (client_fd < 0) {
                std::cerr << "Error: Accept failed" << std::endl;
                continue;
            }

            char client_ip[INET_ADDRSTRLEN];
            inet_ntop(AF_INET, &client_addr.sin_addr, client_ip, INET_ADDRSTRLEN);
            std::cout << "Client connected from " << client_ip << std::endl;

            char buffer[1024]{};
            int bytes_read = recv(client_fd, buffer, sizeof(buffer) - 1, 0);

            if (bytes_read > 0) {
                std::string request(buffer);
                std::cout << "Received: " << request;

                std::string response = handleRequest(request);
                std::cout << "Sending: " << response;

                send(client_fd, response.c_str(), response.length(), 0);
            } else if (bytes_read == 0) {
                std::cout << "Client disconnected" << std::endl;
            } else {
                std::cout << "recv failed" << std::endl;
            }

            close(client_fd);
            std::cout << "Client connection closed\n" << std::endl;
        }

        close(server_fd);
    }
};

int main(int argc, char* argv[]) {
    WordServer server;

    // Parse command line arguments
    if (!server.parseArgs(argc, argv)) {
        std::cerr << "Error parsing arguments" << std::endl;
        return 1;
    }

    std::cout << "Starting word counting server..." << std::endl;

    if (!server.loadConfig()) return 1;
    if (!server.loadWords()) return 1;

    server.run();
    return 0;
}