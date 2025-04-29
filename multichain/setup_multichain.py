import subprocess
import time
import sys
import os
import shutil

CHAIN_NAME = "cosmeticsChain"
STREAMS = ["products", "shipments", "anomalies"]
MULTICHAIN_DIR = os.path.expanduser(f"~/.multichain/{CHAIN_NAME}")

def run(cmd: str):
    print(f"> {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"ERROR running `{cmd}`:\n{e.stderr.decode()}", file=sys.stderr)
        sys.exit(1)

def main():
    # 0) If chain directory exists, stop and remove it
    if os.path.isdir(MULTICHAIN_DIR):
        print(f"Chain directory {MULTICHAIN_DIR} exists. Removing existing chain...")
        # Attempt to stop the running daemon
        try:
            run(f"multichain-cli {CHAIN_NAME} stop")
        except SystemExit:
            print("Daemon may not be running or stop failed; continuing with cleanup.")
        # Wait for shutdown
        time.sleep(5)
        # Delete chain data
        try:
            shutil.rmtree(MULTICHAIN_DIR)
            print(f"Deleted directory {MULTICHAIN_DIR}")
        except Exception as e:
            print(f"Failed to delete {MULTICHAIN_DIR}: {e}", file=sys.stderr)
            sys.exit(1)

    # 1) Create the chain
    run(f"multichain-util create {CHAIN_NAME}")

    # 2) Start the daemon
    run(f"multichaind {CHAIN_NAME} -daemon")

    # 3) Wait for the node to initialize
    print("Waiting 10s for the daemon to start...")
    time.sleep(10)

    # 4) Create streams
    for stream in STREAMS:
        run(f"multichain-cli {CHAIN_NAME} create stream {stream} true")

    # 5) Subscribe to streams
    for stream in STREAMS:
        run(f"multichain-cli {CHAIN_NAME} subscribe {stream}")

    print("✅ Multichain setup complete!")
    print(f"  - Chain: {CHAIN_NAME} ({MULTICHAIN_DIR})")
    print(f"  - Streams: {', '.join(STREAMS)}")

if __name__ == "__main__":
    main()
