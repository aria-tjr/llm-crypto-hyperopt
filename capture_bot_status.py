#!/usr/bin/env python3
"""
Capture bot startup output to show balance and positions
"""
import subprocess
import sys
import time

def capture_bot_startup():
    """Start bot and capture initial output"""
    print("Starting bot to capture account status...\n")
    
    proc = subprocess.Popen(
        ['python', 'src/live_trading.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    lines_captured = []
    start_time = time.time()
    
    try:
        for line in proc.stdout:
            lines_captured.append(line)
            
            # Print lines containing key info
            if any(keyword in line for keyword in [
                'Balance', 'Equity', 'Available', 'Wallet',
                'Found', 'position', 'Leverage',
                'Total', 'STARTING LIVE TRADING'
            ]):
                print(line.rstrip())
            
            # Stop after we see the main trading loop starting
            if 'STARTING LIVE TRADING' in line:
                print("\n✓ Captured startup info. Stopping bot...")
                break
            
            # Safety timeout
            if time.time() - start_time > 30:
                print("\n⚠ Timeout reached. Stopping capture...")
                break
                
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
    
    print(f"\n✓ Captured {len(lines_captured)} lines of output")
    
    # Save full output to file for review
    with open('bot_startup_output.txt', 'w') as f:
        f.writelines(lines_captured)
    print("✓ Full output saved to bot_startup_output.txt")

if __name__ == '__main__':
    capture_bot_startup()
