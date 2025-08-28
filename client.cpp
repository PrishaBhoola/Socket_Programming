#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <map>
#include <vector>
#include <cstring>
#include <chrono>

class WordClient {
private:
    std::string server_ip;
    int server_port;
    int p;  // starting offset
    int k;  // number of words to request

public:
    WordClient() = default;
    ~WordClient() = default;

    // Load configuration from config.json
    bool loadConfig() {
        std::ifstream config_file("config.json");
        if (!config_file.is_open()) {
            std::cerr << "Error: Cannot open config.json" << std::endl;
            return false;
        }

        std::string line;
        while (std::getline(config_file, line)) {
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
            else if (line.find("p") != std::string::npos) {
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
            else if (line.find("k") != std::string::npos) {
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

        std::cout << "Config loaded: " << server_ip << ":" << server_port << std::endl;
        std::cout << "Request parameters: p=" << p << ", k=" << k << std::endl;
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

        std::cout << "\nWord frequencies:" << std::endl;
        for (const auto& pair : word_count) {
            std::cout << pair.first << ", " << pair.second << std::endl;
        }
    }

    // Connect to server and make request
    bool makeRequest() {
        int client_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (client_fd < 0) {
            std::cerr << "Error: Cannot create socket" << std::endl;
            return false;
        }

        struct sockaddr_in server_addr {};
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(server_port);

        if (server_ip == "localhost" || server_ip == "127.0.0.1") {
            server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
        } else {
            if (inet_pton(AF_INET, server_ip.c_str(), &server_addr.sin_addr) <= 0) {
                std::cerr << "Error: Invalid server IP address: " << server_ip << std::endl;
                close(client_fd);
                return false;
            }
        }

        if (connect(client_fd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            std::cerr << "Error: Connection failed" << std::endl;
            close(client_fd);
            return false;
        }

        std::cout << "Connected to server " << server_ip << ":" << server_port << std::endl;

        std::string request = std::to_string(p) + "," + std::to_string(k) + "\n";
        std::cout << "Sending request: " << request;

        if (send(client_fd, request.c_str(), request.length(), 0) < 0) {
            std::cerr << "Error: Failed to send request" << std::endl;
            close(client_fd);
            return false;
        }

        char buffer[4096];
        memset(buffer, 0, sizeof(buffer));

        int bytes_received = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
        if (bytes_received < 0) {
            std::cerr << "Error: Failed to receive response" << std::endl;
            close(client_fd);
            return false;
        }
        else if (bytes_received == 0) {
            std::cout << "Server closed connection" << std::endl;
        }
        else {
            std::string response(buffer);
            std::cout << "Received response: " << response;
            countWordFrequencies(response);
        }

        close(client_fd);
        std::cout << "Connection closed" << std::endl;

        return bytes_received > 0;
    }

    // Run client with timing
    double runWithTiming() {
        auto start_time = std::chrono::high_resolution_clock::now();
        bool success = makeRequest();
        auto end_time = std::chrono::high_resolution_clock::now();

        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
        double completion_time = duration.count() / 1000.0;

        if (success) {
            std::cout << "\nCompletion time: " << completion_time << " ms" << std::endl;
        }

        return success ? completion_time : -1.0;
    }
};

int main(int argc, char* argv[]) {
    WordClient client;
    std::cout << "Starting word counting client..." << std::endl;

    if (!client.loadConfig()) {
        std::cerr << "Failed to load configuration" << std::endl;
        return 1;
    }

    if (argc > 1 && std::string(argv[1]) == "--timing") {
        double completion_time = client.runWithTiming();
        if (completion_time > 0) {
            std::cout << completion_time << std::endl;
        }
        return completion_time > 0 ? 0 : 1;
    }
    else {
        if (client.makeRequest()) {
            std::cout << "\nRequest completed successfully!" << std::endl;
            return 0;
        } else {
            std::cerr << "Request failed!" << std::endl;
            return 1;
        }
    }
}
