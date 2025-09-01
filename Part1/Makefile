# Makefile for Socket Programming Assignment
# Based on instructor requirements

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

# Run single iteration with K and P from environment variables
# Usage: K=10 P=5 make run
run: build
	@echo "=========================================="
	@echo "  Single Iteration Test (Demo Runner)     "
	@echo "=========================================="
	@if [ ! -f config.json ]; then \
		echo "❌ Error: config.json not found"; \
		echo "Please provide config.json before running"; \
		exit 1; \
	fi
	@echo "Using K=$${K:-5} P=$${P:-0} from environment"
	@echo "Running demo with these values..."
	@K=$${K:-5} P=$${P:-0} sudo -E python3 runner.py

# Run analysis experiments for different p and k values
plot: build
	@echo "=========================================="
	@echo "  Analysis Experiments (Different p,k)    "
	@echo "=========================================="
	@if [ ! -f config.json ]; then \
		echo "❌ Error: config.json not found"; \
		echo "Please provide config.json before running"; \
		exit 1; \
	fi
	@echo "Running analysis experiments for different k values..."
	@sudo python3 run_experiments.py
	@echo "Generating plot..."
	@python3 plot_results.py
	@echo "✅ ANALYSIS COMPLETE!"
	@echo "📊 Results: results.csv"
	@echo "📈 Plot: p1_plot.png"

# Check if config exists
setup:
	@echo "Checking configuration..."
	@if [ ! -f config.json ]; then \
		echo "❌ Error: config.json not found"; \
		echo "Please provide config.json with required fields"; \
		exit 1; \
	else \
		echo "✅ config.json found"; \
		echo "Ready for experiments"; \
	fi

# Show config contents
show-config:
	@if [ -f config.json ]; then \
		echo "Contents of config.json:"; \
		cat config.json; \
	else \
		echo "❌ config.json not found"; \
	fi

# Install dependencies
install-deps:
	@echo "Installing Python dependencies..."
	@pip3 install matplotlib numpy
	@echo "✅ Dependencies installed!"

# Clean files
clean:
	@rm -f $(SERVER) $(CLIENT) results.csv p1_plot.png part1_results.csv demo_config.json
	@echo "Cleaned files"

# Help
help:
	@echo "Socket Programming Assignment"
	@echo "============================"
	@echo ""
	@echo "USAGE:"
	@echo "  make run          # Single test with K and P from environment"
	@echo "                    # Example: K=10 P=5 make run"
	@echo "  make plot         # Analysis experiments (different k values)"
	@echo ""
	@echo "SETUP:"
	@echo "  make setup        # Check if config.json exists"
	@echo "  make build        # Compile programs"
	@echo ""
	@echo "ENVIRONMENT VARIABLES for 'make run':"
	@echo "  K     - Number of words to request (default: 5)"
	@echo "  P     - Starting position offset (default: 0)"
	@echo ""
	@echo "EXAMPLES:"
	@echo "  make run                    # Uses K=5, P=0"
	@echo "  K=10 make run              # Uses K=10, P=0"
	@echo "  K=20 P=5 make run          # Uses K=20, P=5"
	@echo ""
	@echo "NOTE: 'make run' is for testing specific cases"
	@echo "      'make plot' is for analysis with multiple k values"

.PHONY: build run plot setup show-config install-deps clean help