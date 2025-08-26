# Makefile for Part 1: TCP Socket Programming
CC = g++
CFLAGS = -std=c++11 -Wall -Wextra

# Executables
SERVER = server
CLIENT = client

# Source files  
SERVER_SRC = server.cpp
CLIENT_SRC = client.cpp

# Build both server and client
build: $(SERVER) $(CLIENT)

$(SERVER): $(SERVER_SRC)
	$(CC) $(CFLAGS) -o $(SERVER) $(SERVER_SRC)

$(CLIENT): $(CLIENT_SRC)  
	$(CC) $(CFLAGS) -o $(CLIENT) $(CLIENT_SRC)

# Run a single iteration
run: build
	@echo "Starting server in background..."
	@./$(SERVER) &
	@SERVER_PID=$$!; \
	sleep 2; \
	echo "Running client..."; \
	./$(CLIENT); \
	echo "Stopping server..."; \
	kill $$SERVER_PID 2>/dev/null || true

# Run with timing for experiments
run-timing: build
	@echo "Starting server in background..."
	@./$(SERVER) &
	@SERVER_PID=$$!; \
	sleep 2; \
	echo "Running client with timing..."; \
	./$(CLIENT) --timing; \
	echo "Stopping server..."; \
	kill $$SERVER_PID 2>/dev/null || true

# Run experiments and generate plot
plot: build
	@echo "Running experiments for different k values..."
	@python3 run_experiments.py

# Clean compiled files
clean:
	@rm -f $(SERVER) $(CLIENT)
	@echo "Cleaned executables"

# Test connection
test: build
	@echo "Testing client-server connection..."
	@./$(SERVER) &
	@SERVER_PID=$$!; \
	sleep 2; \
	echo "Server started, testing client..."; \
	./$(CLIENT) || echo "Client test completed"; \
	kill $$SERVER_PID 2>/dev/null || true; \
	echo "Test finished"

.PHONY: build run run-timing plot clean test