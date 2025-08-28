# Makefile for Linux/WSL Socket Programming
CC = g++
CFLAGS = -std=c++11 -Wall -Wextra
LIBS = 

# Executables
SERVER = server
CLIENT = client

# Source files  
SERVER_SRC = server.cpp
CLIENT_SRC = client.cpp

# Build both server and client
build: $(SERVER) $(CLIENT)
	@echo "Build completed successfully!"

$(SERVER): $(SERVER_SRC)
	@echo "Compiling server..."
	$(CC) $(CFLAGS) -o $(SERVER) $(SERVER_SRC) $(LIBS)
	@echo "Server compiled successfully!"

$(CLIENT): $(CLIENT_SRC)  
	@echo "Compiling client..."
	$(CC) $(CFLAGS) -o $(CLIENT) $(CLIENT_SRC) $(LIBS)
	@echo "Client compiled successfully!"

# Run a single iteration
run: build
	@echo "Starting server in background..."
	@./$(SERVER) &
	@sleep 2
	@echo "Running client..."
	@./$(CLIENT)
	@echo "Stopping server..."
	@pkill -f $(SERVER) || echo "Server stopped"

# Run with timing for experiments
run-timing: build
	@echo "Starting server in background..."
	@./$(SERVER) &
	@sleep 2
	@echo "Running client with timing..."
	@./$(CLIENT) --timing
	@echo "Stopping server..."
	@pkill -f $(SERVER) || echo "Server stopped"

# Clean compiled files
clean:
	@rm -f $(SERVER) $(CLIENT)
	@echo "Cleaned executables"

# Test connection
test: build
	@echo "Testing client-server connection..."
	@./$(SERVER) &
	@sleep 2
	@./$(CLIENT) || echo "Client test completed"
	@pkill -f $(SERVER) || echo "Server stopped"
	@echo "Test finished"

# Setup local config for testing
setup-local:
	@echo Creating local configuration...
	@echo '{' > config.json
	@echo '    "server_ip": "127.0.0.1",' >> config.json
	@echo '    "server_port": 8080,' >> config.json
	@echo '    "filename": "words.txt",' >> config.json
	@echo '    "p": 0,' >> config.json
	@echo '    "k": 5,' >> config.json
	@echo '    "num_repetitions": 5' >> config.json
	@echo '}' >> config.json
	@echo Local config created!

# Help target
help:
	@echo Available targets:
	@echo "  build       - Compile server and client"
	@echo "  run         - Run one iteration of client-server"
	@echo "  run-timing  - Run client with timing measurement"
	@echo "  test        - Basic connection test"
	@echo "  clean       - Remove compiled executables"
	@echo "  setup-local - Create local testing configuration"
	@echo "  help        - Show this help"

.PHONY: build run run-timing clean test setup-local help
