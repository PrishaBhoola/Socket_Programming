# Makefile for Greedy Client FCFS Fairness Analysis (Part 3)

.PHONY: all setup test single run plot clean help

# Default target
all: help

# Setup files and configuration
setup:
	@echo "Setting up greedy client fairness experiment..."
	@python3 runner.py --setup
	@echo "✅ Setup complete"

# Test basic functionality
test:
	@echo "Testing greedy client fairness (requires sudo)..."
	@sudo python3 runner.py --clients 5 --c 3
	@echo "✅ Test complete"

# Run single FCFS experiment  
single:
	@echo "Running single FCFS fairness experiment (requires sudo)..."
	@sudo python3 runner.py
	@echo "✅ FCFS experiment complete"

# Run full experimental suite
run:
	@echo "Running full greedy client fairness experiments (requires sudo)..."
	@sudo python3 run_experiments.py
	@echo "✅ Fairness experiments complete"

# Generate fairness analysis plots
plot:
	@echo "Generating fairness analysis plots..."
	@python3 plot.py
	@echo "✅ Plots generated"

# Interactive Mininet mode
interactive:
	@echo "Starting interactive Mininet for manual testing..."
	@sudo python3 topology.py

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -f fairness_results.csv *.png *.pdf server.log
	@rm -rf __pycache__
	@sudo mn -c 2>/dev/null || echo "Mininet cleanup completed"
	@echo "✅ Clean complete"

# Analyze existing results
analyze:
	@echo "Analyzing existing fairness results..."
	@python3 run_experiments.py --analyze
	@echo "✅ Analysis complete"

# Create sample config
config:
	@echo "Creating sample config.json..."
	@echo '{' > config.json
	@echo '    "server_ip": "10.0.0.100",' >> config.json
	@echo '    "port": 8887,' >> config.json
	@echo '    "num_clients": 10,' >> config.json
	@echo '    "c": 10,' >> config.json
	@echo '    "p": 0,' >> config.json
	@echo '    "k": 5' >> config.json
	@echo '}' >> config.json
	@echo "✅ Created config.json"

# Help
help:
	@echo "Greedy Client FCFS Fairness Analysis (Part 3)"
	@echo ""
	@echo "This analyzes fairness when one client sends multiple requests"
	@echo "in a First-Come-First-Serve system."
	@echo ""
	@echo "Available targets:"
	@echo "  setup       - Setup default files and configuration"
	@echo "  config      - Create sample config.json"
	@echo "  test        - Run basic fairness test (requires sudo)"
	@echo "  single      - Run single FCFS experiment (requires sudo)"
	@echo "  run         - Run full experimental suite (requires sudo)"
	@echo "  plot        - Generate fairness analysis plots"
	@echo "  interactive - Start interactive Mininet session"
	@echo "  analyze     - Analyze existing results"
	@echo "  clean       - Clean generated files"
	@echo ""
	@echo "Quick workflow:"
	@echo "  make setup   # Setup files"
	@echo "  make config  # Create config (optional)" 
	@echo "  make test    # Basic test"
	@echo "  make run     # Full experiments"
	@echo "  make plot    # Generate analysis"
	@echo ""
	@echo "Manual testing:"
	@echo "  make interactive  # Start Mininet CLI"
	@echo "  # In CLI:"
	@echo "  #   server python3 server.py &"
	@echo "  #   client1 python3 client.py --client-id client1 --greedy --c 5"  
	@echo "  #   client2 python3 client.py --client-id client2"
