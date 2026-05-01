# Trading Bot — Binance Futures Testnet (USDT-M)

## Project Overview
This project is a CLI-based Python trading bot for placing Binance Futures Testnet (USDT-M) orders using direct REST API calls. It supports MARKET, LIMIT, and STOP-LIMIT style order placement with structured validation, layered architecture, and rotating log files for API activity.

## Prerequisites
- Python 3.10+
- pip

## Binance Testnet Setup
1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your GitHub account
3. Navigate to **Account → API Key**
4. Click **Generate**
5. Copy both your API key and secret immediately
6. Add them to your local `.env` file

## Installation
```bash
git clone <repo>
cd trading_bot
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
