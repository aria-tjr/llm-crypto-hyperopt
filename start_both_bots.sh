#!/bin/bash
# Start both trading bot instances

echo "=================================="
echo "Starting Trading Bots"
echo "=================================="
echo ""

# Check if bots are already running
BOT1_RUNNING=$(pgrep -f "python src/live_trading.py" | grep -v "CONFIG_FILE=src/config2.ini")
BOT2_RUNNING=$(pgrep -f "CONFIG_FILE=src/config2.ini")

if [ ! -z "$BOT1_RUNNING" ]; then
    echo "⚠️  Bot 1 already running (PID: $BOT1_RUNNING)"
else
    echo "🚀 Starting Bot 1 (Account 1: snbEe1...)..."
    nohup python src/live_trading.py > bot1.log 2>&1 &
    BOT1_PID=$!
    echo "   ✅ Bot 1 started with PID: $BOT1_PID"
fi

sleep 2

if [ ! -z "$BOT2_RUNNING" ]; then
    echo "⚠️  Bot 2 already running (PID: $BOT2_RUNNING)"
else
    echo "🚀 Starting Bot 2 (Account 2: pzYRPP...)..."
    CONFIG_FILE=src/config2.ini nohup python src/live_trading.py > bot2.log 2>&1 &
    BOT2_PID=$!
    echo "   ✅ Bot 2 started with PID: $BOT2_PID"
fi

echo ""
echo "=================================="
echo "Both bots started!"
echo "=================================="
echo ""
echo "Monitor logs:"
echo "  Bot 1: tail -f bot1.log"
echo "  Bot 2: tail -f bot2.log"
echo ""
echo "Check status:"
echo "  ps aux | grep 'python src/live_trading.py'"
echo ""
echo "Stop bots:"
echo "  killall python  # (stops all Python processes)"
echo ""
