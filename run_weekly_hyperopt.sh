#!/bin/bash
# Weekly Hyperopt Runner
# Runs every Sunday at 2 AM to optimize parameters on last 30 days
# Schedule with: crontab -e
# Add line: 0 2 * * 0 /Users/ariatajeri/llm_crypto/run_weekly_hyperopt.sh >> /Users/ariatajeri/llm_crypto/weekly_hyperopt.log 2>&1

echo "==========================================="
echo "🔬 WEEKLY HYPEROPT STARTED"
echo "Date: $(date)"
echo "==========================================="

# Navigate to project directory
cd /Users/ariatajeri/llm_crypto

# Stop the trading bot if running
echo "Stopping trading bot..."
pkill -f "python src/live_trading.py" || echo "Bot not running"
sleep 5

# Run intensive hyperopt
echo "Starting intensive hyperopt (300 trials, 30-day window)..."
python run_weekly_hyperopt.py

# Extract best parameters
if [ -f "best_params_weekly.json" ]; then
    echo "✅ Hyperopt completed successfully"
    echo "📊 Best parameters saved to best_params_weekly.json"
    
    # Backup previous parameters
    if [ -f "src/config_params.json" ]; then
        cp src/config_params.json src/config_params_backup_$(date +%Y%m%d).json
    fi
    
    # Update config with new parameters
    cp best_params_weekly.json src/config_params.json
    
    echo "✅ Parameters updated in src/config_params.json"
else
    echo "❌ Hyperopt failed - no parameters file generated"
    exit 1
fi

# Restart trading bot with new parameters
echo "Restarting trading bot..."
nohup python src/live_trading.py > trading_bot.log 2>&1 &
echo "✅ Trading bot restarted with PID: $!"

echo "==========================================="
echo "🎯 WEEKLY HYPEROPT COMPLETED"
echo "Date: $(date)"
echo "==========================================="
