.PHONY: run plot clean setup local mininet help

# Load configuration
CONFIG_FILE = config.json
NUM_CLIENTS = $(shell python3 -c "import json; print(json.load(open('$(CONFIG_FILE)'))['num_clients'])" 2>/dev/null || echo "5")
NUM_REPETITIONS = $(shell python3 -c "import json; print(json.load(open('$(CONFIG_FILE)'))['num_repetitions'])" 2>/dev/null || echo "5")

# Default target
all: help

# Setup requirements and generate test data
setup:
	@echo "Setting up experiment environment..."
	@python3 -c "import socket, json, threading, time, sys, subprocess, csv" 2>/dev/null || \
	(echo "Missing required packages for basic functionality"; exit 1)
	@python3 -c "import pandas, matplotlib, numpy, scipy" 2>/dev/null || \
	echo "Warning: Missing plotting packages. Install with: pip3 install pandas matplotlib numpy scipy"
	@python3 -c "import mininet" 2>/dev/null || \
	echo "Warning: Mininet not found. Install with: sudo apt-get install mininet"
	@echo "Setup complete!"

# Run single experiment locally (for testing)
local: setup
	@echo "Running local experiment with $(NUM_CLIENTS) clients..."
	@python3 generate_words.py local
	@cp config_local.json config.json
	@python3 server.py &
	@SERVER_PID=$$!; \
	sleep 2; \
	python3 run_single_experiment.py; \
	kill $$SERVER_PID 2>/dev/null || true

# Run single experiment in Mininet
run: setup
	@echo "Running Mininet experiment with $(NUM_CLIENTS) clients..."
	@sudo python3 mininet_topology.py

# Run experiments with varying number of clients and generate plot (Mininet)
plot: setup
	@echo "Running Mininet experiments with $(NUM_REPETITIONS) repetitions each..."
	@sudo python3 mininet_topology.py plot
	@python3 plot_results.py

# Run experiments locally (for development/testing)
plot-local: setup
	@echo "Running local experiments with $(NUM_REPETITIONS) repetitions each..."
	@python3 generate_words.py local
	@cp config_local.json config.json
	@python3 run_experiments.py
	@python3 plot_results.py

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -f results.csv p2_plot.png
	@rm -f config_local.json config_mininet.json
	@rm -f words.txt
	@sudo mn -c 2>/dev/null || true

# Test Mininet connectivity
test-mininet:
	@echo "Testing Mininet setup..."
	@sudo python3 -c "from mininet.net import Mininet; from mininet.topo import SingleSwitchTopo; net = Mininet(SingleSwitchTopo(2)); net.start(); print('Mininet working!'); net.stop()"

# Help
help:
	@echo "Word Counter Concurrent Performance Analysis"
	@echo "=========================================="
	@echo ""
	@echo "Available targets:"
	@echo "  setup       - Install requirements and generate test data"
	@echo "  run         - Run single experiment in Mininet ($(NUM_CLIENTS) clients)"
	@echo "  plot        - Run experiments with varying clients in Mininet and generate plot"
	@echo "  local       - Run single experiment locally (for testing)"
	@echo "  plot-local  - Run experiments locally and generate plot (for testing)"
	@echo "  test-mininet- Test if Mininet is working"
	@echo "  clean       - Remove generated files"
	@echo "  help        - Show this help"
	@echo ""
	@echo "Current configuration:"
	@echo "  Clients: $(NUM_CLIENTS)"
	@echo "  Repetitions: $(NUM_REPETITIONS)"
	@echo ""
	@echo "Note: 'run' and 'plot' require sudo for Mininet"