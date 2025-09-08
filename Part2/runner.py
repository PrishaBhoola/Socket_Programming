#!/usr/bin/env python3
"""
Single experiment runner for Mininet concurrent file download testing
Runs experiments in Mininet environment using the specified topology
Server: 10.0.0.100, Clients: 10.0.0.1, 10.0.0.2, etc.
"""

import subprocess
import sys
import time
import json
import os
import re
from pathlib import Path
import argparse

def load_config(config_file='config.json'):
    """Load experiment configuration"""
    try:
        with Path(config_file).open() as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def create_default_config():
    """Create default configuration if none exists"""
    config = {
        "server_ip": "10.0.0.100",
        "server_port": 5000,
        "k": 10,
        "filename": "words.txt",
        "num_clients": 5,
        "num_repetitions": 3
    }

    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

    print("Created default config.json")
    return config

def create_default_words_file():
    """Create default words file if none exists"""
    if not Path('words.txt').exists():
        # Create a substantial word file for testing
        words = []
        for i in range(200):  # 200 words for good testing
            words.append(f"word_{i:03d}")

        content = ','.join(words)
        with open('words.txt', 'w') as f:
            f.write(content)

        print(f"Created words.txt with {len(words)} words")

def validate_environment():
    """Validate that required files exist"""
    required_files = ['server.py', 'client.py', 'topology.py']
    missing_files = []

    for filename in required_files:
        if not Path(filename).exists():
            missing_files.append(filename)

    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False

    print("✅ All required files present")
    return True

def check_mininet_available():
    """Check if Mininet is available"""
    try:
        from mininet.net import Mininet
        from mininet.node import OVSSwitch
        from mininet.link import TCLink
        return True
    except ImportError as e:
        print(f"❌ Mininet not available: {e}")
        print("Please install Mininet or run in a Mininet-enabled environment")
        return False

def setup_experiment_files(net):
    """Copy experiment files to hosts in the network"""
    print("Setting up experiment files...")

    # Files to copy
    files = ['server.py', 'client.py', 'config.json', 'words.txt']

    # Setup server
    server = net.get('server')
    server.cmd('mkdir -p /tmp/experiment')
    for filename in files:
        if Path(filename).exists():
            server.cmd(f'cp {filename} /tmp/experiment/')
            print(f"  Copied {filename} to server")
        else:
            print(f"  Warning: {filename} not found for server")

    # Setup clients  
    for host in net.hosts:
        if host.name.startswith('client'):
            host.cmd('mkdir -p /tmp/experiment')
            for filename in ['client.py', 'config.json']:
                if Path(filename).exists():
                    host.cmd(f'cp {filename} /tmp/experiment/')

    print("✅ File setup complete")

def start_server(net):
    """Start the server"""
    print("Starting server...")
    server = net.get('server')

    # Start server in background
    server.cmd('cd /tmp/experiment && python3 server.py > server.log 2>&1 &')
    time.sleep(3)  # Give server time to start

    # Check if server started
    result = server.cmd('ps aux | grep "python3 server.py" | grep -v grep')
    if result.strip():
        print("✅ Server started successfully")
        return True
    else:
        print("❌ Server failed to start")
        log = server.cmd('cat /tmp/experiment/server.log 2>/dev/null || echo "No log file"')
        print(f"Server log: {log}")
        return False

def stop_server(net):
    """Stop the server"""
    print("Stopping server...")
    server = net.get('server')
    server.cmd('pkill -f "python3 server.py"')
    time.sleep(1)

def run_experiment(net, num_clients):
    """Run the actual experiment"""
    print(f"Running experiment with {num_clients} clients...")

    # Start all clients
    for i in range(1, num_clients + 1):
        client = net.get(f'client{i}')
        if client:
            cmd = f'cd /tmp/experiment && python3 client.py --quiet --client-id client{i} > client{i}_result.txt 2>&1 &'
            client.cmd(cmd)
            print(f"  Started client{i}")
        else:
            print(f"  Warning: client{i} not found in network")

    # Wait for completion
    print("Waiting for clients to complete...")
    max_wait = 60
    elapsed = 0

    while elapsed < max_wait:
        all_done = True
        for i in range(1, num_clients + 1):
            client = net.get(f'client{i}')
            if client:
                result = client.cmd('ps aux | grep "python3 client.py" | grep -v grep')
                if result.strip():
                    all_done = False
                    break

        if all_done:
            print("✅ All clients completed")
            break

        time.sleep(2)
        elapsed += 2

        if elapsed % 10 == 0:
            print(f"  Still waiting... ({elapsed}s elapsed)")

    # Collect results
    results = []
    print("\nCollecting results...")

    for i in range(1, num_clients + 1):
        client = net.get(f'client{i}')
        if client:
            output = client.cmd(f'cat /tmp/experiment/client{i}_result.txt 2>/dev/null || echo "No output"')

            if "ELAPSED_MS:" in output:
                try:
                    elapsed_ms = float(output.split("ELAPSED_MS:")[1].split()[0])
                    results.append(elapsed_ms)
                    print(f"  client{i}: {elapsed_ms:.3f} ms")
                except Exception as e:
                    print(f"  client{i}: Failed to parse result - {e}")
            else:
                print(f"  client{i}: No completion time found")
                if len(output.strip()) > 0 and output != "No output":
                    print(f"    Output: {output.strip()[:100]}")

    return results

def run_mininet_experiment(num_clients, verbose=True):
    """Run experiment using Mininet"""
    if verbose:
        print(f"\n=== RUNNING MININET EXPERIMENT ===")
        print(f"Number of clients: {num_clients}")
        print(f"Server: 10.0.0.100:5000")
        print(f"Clients: 10.0.0.1 to 10.0.0.{num_clients}")

    # Make sure config has correct IP
    config = load_config()
    if config.get('server_ip') != '10.0.0.100':
        config['server_ip'] = '10.0.0.100'
        config['num_clients'] = num_clients
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Updated config for Mininet")

    try:
        # Import Mininet and our topology
        from mininet.net import Mininet
        from mininet.node import OVSSwitch  
        from mininet.link import TCLink
        from mininet.log import setLogLevel
        from topology import SimpleTopo  # Only import the topology class

        if not verbose:
            setLogLevel('warning')
        else:
            setLogLevel('info')

        # Create network using simple topology
        if verbose:
            print("Creating Mininet network...")

        topo = SimpleTopo(num_clients)
        net = Mininet(topo=topo, switch=OVSSwitch, link=TCLink)
        net.start()

        if verbose:
            print("✅ Network started successfully")
            print("Network topology:")
            for host in net.hosts:
                print(f"  {host.name}: {host.IP()}")

        try:
            # Setup experiment files
            setup_experiment_files(net)

            # Start server
            if start_server(net):
                # Run the actual experiment
                results = run_experiment(net, num_clients)

                if results and verbose:
                    avg_time = sum(results) / len(results)
                    min_time = min(results)
                    max_time = max(results)

                    print(f"\n=== EXPERIMENT RESULTS ===")
                    print(f"Successful downloads: {len(results)}/{num_clients}")
                    print(f"Average completion time: {avg_time:.3f} ms")
                    print(f"Range: {min_time:.3f} - {max_time:.3f} ms")

                    if len(results) > 1:
                        spread = max_time - min_time
                        print(f"Performance spread: {spread:.3f} ms")

                        if spread > avg_time * 0.2:
                            print("✅ Observed performance variation suggests FIFO queueing")
                        else:
                            print("⚠️ Limited performance variation - may need more clients")

                return results
            else:
                print("❌ Server failed to start")
                return []

        finally:
            stop_server(net)
            net.stop()
            if verbose:
                print("Network stopped")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Check that topology.py contains SimpleTopo class")
        return []
    except Exception as e:
        print(f"❌ Experiment failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return []

def main():
    parser = argparse.ArgumentParser(description='Mininet experiment runner')
    parser.add_argument('--clients', type=int, help='Number of clients')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    parser.add_argument('--setup', action='store_true', help='Setup default files')

    args = parser.parse_args()

    if args.setup:
        print("Setting up default files for Mininet experiments...")
        create_default_config()
        create_default_words_file()
        print("✅ Setup complete")
        return

    # Validate environment
    if not validate_environment():
        print("\nRun with --setup to create default files")
        sys.exit(1)

    if not check_mininet_available():
        print("\nMininet is required for this experiment")
        sys.exit(1)

    # Ensure config and words files exist
    if not Path('config.json').exists():
        create_default_config()
    if not Path('words.txt').exists():
        create_default_words_file()

    # Get number of clients
    config = load_config()
    num_clients = args.clients or config.get('num_clients', 5)

    if not args.quiet:
        print(f"🔬 Running Mininet experiment with {num_clients} clients")

    # Run the experiment
    results = run_mininet_experiment(num_clients, not args.quiet)

    # Report results
    if results:
        avg_time = sum(results) / len(results)
        success_rate = len(results) / num_clients

        if args.quiet:
            print(f"SUCCESS:{len(results)}/{num_clients}:{avg_time:.3f}")
        else:
            print(f"\n✅ Experiment completed successfully!")
            print(f"   📊 {len(results)}/{num_clients} clients completed downloads")
            print(f"   ⏱️ Average completion time: {avg_time:.3f} ms")
            print(f"   📈 Success rate: {success_rate:.1%}")
            print(f"SUCCESS:")
    else:
        if args.quiet:
            print(f"FAILED:0/{num_clients}:0.0")
        else:
            print(f"\n❌ Experiment failed - no successful downloads")
            print(f"\nTroubleshooting:")
            print(f"   1. Check server starts: python3 server.py")
            print(f"   2. Verify Mininet: sudo mn --test pingall")
            print(f"   3. Check files: ls -la server.py client.py words.txt")
            print(f"   4. Try manual test: sudo python3 topology.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
