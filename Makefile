# Makefile for Part 1: Socket Programming Assignment
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
	@echo "Build completed successfully!"

$(SERVER): $(SERVER_SRC)
	@echo "Compiling server..."
	$(CC) $(CFLAGS) -o $(SERVER) $(SERVER_SRC)

$(CLIENT): $(CLIENT_SRC)  
	@echo "Compiling client..."
	$(CC) $(CFLAGS) -o $(CLIENT) $(CLIENT_SRC)

# Run experiments using the official starter code approach
plot: build
	@echo "=========================================="
	@echo "  Part 1: Socket Programming Experiments  "
	@echo "=========================================="
	@echo "Ensuring Mininet config..."
	@make setup-mininet
	@echo "Running experiments (this may take a few minutes)..."
	@sudo python3 run_experiments.py
	@echo "Generating plot..."
	@python3 plot_results.py
	@echo "✅ EXPERIMENT COMPLETE!"
	@echo "📊 Raw results: results.csv"
	@echo "📈 Plot: p1_plot.png"
	@echo "📁 Ready for submission!"

# Run a single iteration (LOCAL TESTING)
run: build
	@echo "Setting up localhost config for testing..."
	@make setup-local
	@echo "Starting server in background..."
	@./$(SERVER) --config config.json &
	@sleep 2
	@echo "Running client..."
	@./$(CLIENT) --config config.json
	@echo "Stopping server..."
	@pkill -f $(SERVER) || echo "Server stopped"

# Setup for local testing (localhost)
setup-local:
	@echo "Creating localhost configuration..."
	@echo '{' > config.json
	@echo '    "server_ip": "127.0.0.1",' >> config.json
	@echo '    "server_port": 8080,' >> config.json
	@echo '    "filename": "words.txt",' >> config.json
	@echo '    "p": 0,' >> config.json
	@echo '    "k": 5,' >> config.json
	@echo '    "num_repetitions": 5' >> config.json
	@echo '}' >> config.json
	@echo "Local config created (127.0.0.1:8080)!"

# Setup for Mininet experiments
setup-mininet:
	@echo "Creating Mininet configuration..."
	@echo '{' > config.json
	@echo '    "server_ip": "10.0.0.2",' >> config.json
	@echo '    "server_port": 5000,' >> config.json
	@echo '    "filename": "words.txt",' >> config.json
	@echo '    "p": 0,' >> config.json
	@echo '    "k": 5,' >> config.json
	@echo '    "num_repetitions": 5' >> config.json
	@echo '}' >> config.json
	@echo "Mininet config created (10.0.0.2:5000)!"

# Test the topology
test-topo:
	@python3 topo_wordcount.py

# Clean files
clean:
	@rm -f $(SERVER) $(CLIENT) results.csv p1_plot.png part1_results.csv
	@echo "Cleaned files"

# Help
help:
	@echo "Assignment Part 1 Targets:"
	@echo "========================="
	@echo "REQUIRED:"
	@echo "  build           - Compile programs"
	@echo "  run             - Single test (localhost)"
	@echo "  plot            - Run experiments + generate plot (Mininet)"
	@echo ""
	@echo "SETUP:"
	@echo "  setup-local     - Config for localhost testing"
	@echo "  setup-mininet   - Config for Mininet experiments"
	@echo "  test-topo       - Test network topology"
	@echo ""
	@echo "WORKFLOW:"
	@echo "  For local testing: make run"
	@echo "  For experiments: make plot"

.PHONY: build run plot setup-local setup-mininet test-topo clean help