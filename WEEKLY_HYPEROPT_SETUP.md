# Weekly Hyperopt Scheduler Setup Instructions

## Overview
Automatically runs hyperopt every Sunday at 2 AM to optimize parameters on the last 30 days of data.

## Setup Steps

### 1. Make the script executable (already done)
```bash
chmod +x run_weekly_hyperopt.sh
```

### 2. Set up cron job

Open crontab editor:
```bash
crontab -e
```

Add this line (schedule for Sundays at 2 AM):
```
0 2 * * 0 /Users/ariatajeri/llm_crypto/run_weekly_hyperopt.sh >> /Users/ariatajeri/llm_crypto/weekly_hyperopt.log 2>&1
```

Save and exit (`:wq` in vim or `Ctrl+X` then `Y` in nano)

### 3. Verify cron job is set
```bash
crontab -l
```

## How It Works

1. **Every Sunday at 2:00 AM**, the cron job triggers
2. **Stops the trading bot** (if running)
3. **Runs intensive hyperopt** (300 trials, ~30-45 minutes)
   - Optimizes on last 30 days of data
   - Tests 15 top-quality assets
   - Searches for best: leverage (5-10x), threshold (0.3-0.7), stop loss (1.5-3.5%), take profit (8-15%)
4. **Saves best parameters** to `best_params_weekly.json`
5. **Updates configuration** in `src/config_params.json`
6. **Restarts trading bot** with new optimized parameters
7. **Logs everything** to `weekly_hyperopt.log`

## Manual Test Run

To test the hyperopt without waiting for Sunday:
```bash
./run_weekly_hyperopt.sh
```

Or run just the Python optimization:
```bash
python run_weekly_hyperopt.py
```

## Monitoring

Check the log file to see optimization results:
```bash
tail -f weekly_hyperopt.log
```

Check latest best parameters:
```bash
cat best_params_weekly.json
```

## Cron Schedule Syntax
```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, 0 or 7 = Sunday)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

Examples:
- `0 2 * * 0` - Every Sunday at 2:00 AM
- `0 2 * * 1` - Every Monday at 2:00 AM
- `0 3 * * *` - Every day at 3:00 AM
- `0 */6 * * *` - Every 6 hours

## Troubleshooting

### Cron job not running?
1. Check cron is enabled: `sudo launchctl list | grep cron`
2. Check system logs: `grep CRON /var/log/system.log`
3. Verify path: `which python` (update script if needed)

### Bot not restarting?
Check if it's running:
```bash
ps aux | grep "python src/live_trading.py"
```

Manually restart:
```bash
nohup python src/live_trading.py > trading_bot.log 2>&1 &
```

### Hyperopt fails?
Check the log:
```bash
cat weekly_hyperopt.log
```

Test manually:
```bash
python run_weekly_hyperopt.py
```

## Disable Weekly Hyperopt

To stop automatic optimization:
```bash
crontab -e
```

Comment out or delete the line:
```
# 0 2 * * 0 /Users/ariatajeri/llm_crypto/run_weekly_hyperopt.sh >> /Users/ariatajeri/llm_crypto/weekly_hyperopt.log 2>&1
```

## Next Steps

After setup is complete, the system will:
1. ✅ Run at 10x max leverage (prevents liquidations)
2. ✅ Adapt threshold hourly based on volatility
3. ✅ Enforce $50/day loss limit per symbol
4. ✅ Exclude volatile small-caps (BIRB, ANIME, etc.)
5. ✅ Re-optimize weekly with fresh data

Your bot is now running with professional-grade risk management! 🎯
