#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    #define close closesocket
    typedef int socklen_t;

    // Fallback implementations for older MinGW versions
    #ifndef INET_ADDRSTRLEN
    #define INET_ADDRSTRLEN 16
    #endif

    // Check if inet_pton is available, if not provide fallback
    #if !defined(inet_pton) && (_WIN32_WINNT < 0x0600)
    int inet_pton_fallback(int af, const char *src, void *dst) {
        if (af == AF_INET) {
            unsigned long addr = inet_addr(src);
            if (addr == INADDR_NONE && strcmp(src, "255.255.255.255") != 0) {
                return 0; // Invalid format
            }
            memcpy(dst, &addr, sizeof(addr));
            return 1; // Success
        }
        return -1; // Unsupported family
    }
    #define inet_pton inet_pton_fallback
    #endif

    // Check if inet_ntop is available, if not provide fallback
    #if !defined(inet_ntop) && (_WIN32_WINNT < 0x0600)
    const char* inet_ntop_fallback(int af, const void *src, char *dst, socklen_t size) {
        if (af == AF_INET && size >= INET_ADDRSTRLEN) {
            struct in_addr addr;
            memcpy(&addr, src, sizeof(addr));
            char* str = inet_ntoa(addr);
            if (str) {
                strcpy(dst, str);
                return dst;
            }
        }
        return NULL;
    }
    #define inet_ntop inet_ntop_fallback
    #endif

#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
#endif

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

#ifdef _WIN32
    WSADATA wsaData;
    bool winsockInitialized;
#endif

public:
    WordClient() {
#ifdef _WIN32
        winsockInitialized = false;
        // Initialize Winsock
        int result = WSAStartup(MAKEWORD(2,2), &wsaData);
        if (result != 0) {
            std::cerr << "WSAStartup failed with error: " << result << std::endl;
        } else {
            winsockInitialized = true;
            std::cout << "Winsock initialized successfully" << std::endl;
        }
#endif
    }

    ~WordClient() {
#ifdef _WIN32
        if (winsockInitialized) {
            WSACleanup();
        }
#endif
    }

    // Load configuration from config.json
    bool loadConfig() {
        std::ifstream config_file("config.json");
        if (!config_file.is_open()) {
            std::cerr << "Error: Cannot open config.json" << std::endl;
            return false;
        }

        std::string line;
        while (std::getline(config_file, line)) {
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
                // Remove any non-numeric characters
                std::string clean_port;
                for (char c : port_str) {
                    if (isdigit(c)) {
                        clean_port += c;
                    }
                }
                if (!clean_port.empty()) {
                    server_port = std::stoi(clean_port);
                }
            }
            else if (line.find("p") != std::string::npos) {
                size_t start = line.find(":") + 1;
                std::string p_str = line.substr(start);
                // Remove any non-numeric characters
                std::string clean_p;
                for (char c : p_str) {
                    if (isdigit(c)) {
                        clean_p += c;
                    }
                }
                if (!clean_p.empty()) {
                    p = std::stoi(clean_p);
                }
            }
            else if (line.find("k") != std::string::npos) {
                size_t start = line.find(":") + 1;
                std::string k_str = line.substr(start);
                // Remove any non-numeric characters
                std::string clean_k;
                for (char c : k_str) {
                    if (isdigit(c)) {
                        clean_k += c;
                    }
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

        // Remove newline from response
        std::string clean_response = words_response;
        clean_response.erase(clean_response.find_last_not_of("\n\r") + 1);

        // Parse comma-separated words
        std::stringstream ss(clean_response);
        std::string word;

        while (std::getline(ss, word, ',')) {
            // Remove whitespace
            word.erase(0, word.find_first_not_of(" \t"));
            word.erase(word.find_last_not_of(" \t") + 1);

            // Skip EOF token
            if (word == "EOF") {
                continue;
            }

            if (!word.empty()) {
                word_count[word]++;
            }
        }

        // Print word frequencies
        std::cout << "\nWord frequencies:" << std::endl;
        for (const auto& pair : word_count) {
            std::cout << pair.first << ", " << pair.second << std::endl;
        }
    }

    // Connect to server and make request
    bool makeRequest() {
#ifdef _WIN32
        if (!winsockInitialized) {
            std::cerr << "Error: Winsock not initialized" << std::endl;
            return false;
        }
#endif

        // Create socket
#ifdef _WIN32
        SOCKET client_fd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (client_fd == INVALID_SOCKET) {
            std::cerr << "Error: Cannot create socket. Error: " << WSAGetLastError() << std::endl;
            return false;
        }
#else
        int client_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (client_fd < 0) {
            std::cerr << "Error: Cannot create socket" << std::endl;
            return false;
        }
#endif

        // Setup server address
        struct sockaddr_in server_addr;
        memset(&server_addr, 0, sizeof(server_addr));
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(server_port);

        // Convert IP address - use simpler approach for Windows compatibility
        if (server_ip == "localhost" || server_ip == "127.0.0.1") {
            server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
        } else {
            // Try inet_pton first, fallback to inet_addr
            if (inet_pton(AF_INET, server_ip.c_str(), &server_addr.sin_addr) <= 0) {
                // Fallback to inet_addr
                unsigned long addr = inet_addr(server_ip.c_str());
                if (addr == INADDR_NONE) {
                    std::cerr << "Error: Invalid server IP address: " << server_ip << std::endl;
                    close(client_fd);
                    return false;
                } else {
                    server_addr.sin_addr.s_addr = addr;
                }
            }
        }

        // Connect to server
        if (connect(client_fd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
#ifdef _WIN32
            std::cerr << "Error: Connection failed. Error: " << WSAGetLastError() << std::endl;
#else
            std::cerr << "Error: Connection failed" << std::endl;
#endif
            close(client_fd);
            return false;
        }

        std::cout << "Connected to server " << server_ip << ":" << server_port << std::endl;

        // Prepare request message
        std::string request = std::to_string(p) + "," + std::to_string(k) + "\n";
        std::cout << "Sending request: " << request;

        // Send request
        if (send(client_fd, request.c_str(), (int)request.length(), 0) < 0) {
#ifdef _WIN32
            std::cerr << "Error: Failed to send request. Error: " << WSAGetLastError() << std::endl;
#else
            std::cerr << "Error: Failed to send request" << std::endl;
#endif
            close(client_fd);
            return false;
        }

        // Receive response
        char buffer[4096];
        memset(buffer, 0, sizeof(buffer));

        int bytes_received = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
        if (bytes_received < 0) {
#ifdef _WIN32
            std::cerr << "Error: Failed to receive response. Error: " << WSAGetLastError() << std::endl;
#else
            std::cerr << "Error: Failed to receive response" << std::endl;
#endif
            close(client_fd);
            return false;
        }
        else if (bytes_received == 0) {
            std::cout << "Server closed connection" << std::endl;
        }
        else {
            std::string response(buffer);
            std::cout << "Received response: " << response;

            // Process the response
            countWordFrequencies(response);
        }

        // Close connection
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
        double completion_time = duration.count() / 1000.0; // Convert to milliseconds

        if (success) {
            std::cout << "\nCompletion time: " << completion_time << " ms" << std::endl;
        }

        return success ? completion_time : -1.0;
    }
};

int main(int argc, char* argv[]) {
    WordClient client;

    std::cout << "Starting word counting client..." << std::endl;

    // Load configuration
    if (!client.loadConfig()) {
        std::cerr << "Failed to load configuration" << std::endl;
        return 1;
    }

    // Check if we want timing mode (for experiments)
    if (argc > 1 && std::string(argv[1]) == "--timing") {
        double completion_time = client.runWithTiming();
        if (completion_time > 0) {
            // Output just the timing for script processing
            std::cout << completion_time << std::endl;
        }
        return completion_time > 0 ? 0 : 1;
    }
    else {
        // Normal mode - make request and show results
        if (client.makeRequest()) {
            std::cout << "\nRequest completed successfully!" << std::endl;
            return 0;
        } else {
            std::cerr << "Request failed!" << std::endl;
            return 1;
        }
    }
}