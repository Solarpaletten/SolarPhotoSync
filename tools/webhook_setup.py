#!/usr/bin/env python3
"""
SOLAR PhotoSync v1.0 - Webhook Setup Utility
Утилита для настройки Telegram Webhook
"""

import sys
import json
import argparse
import requests
from pathlib import Path


def load_config(config_path: str = None) -> dict:
    """Загрузить конфигурацию"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "photosync.config.json"
    
    with open(config_path, 'r') as f:
        return json.load(f)


def set_webhook(token: str, url: str, secret: str = None) -> dict:
    """Установить webhook"""
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    
    params = {
        "url": url,
        "allowed_updates": ["message"],
        "drop_pending_updates": True
    }
    
    if secret:
        params["secret_token"] = secret
    
    response = requests.post(api_url, json=params)
    return response.json()


def delete_webhook(token: str) -> dict:
    """Удалить webhook"""
    api_url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    
    params = {"drop_pending_updates": True}
    
    response = requests.post(api_url, json=params)
    return response.json()


def get_webhook_info(token: str) -> dict:
    """Получить информацию о webhook"""
    api_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    response = requests.get(api_url)
    return response.json()


def get_me(token: str) -> dict:
    """Получить информацию о боте"""
    api_url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(api_url)
    return response.json()


def main():
    parser = argparse.ArgumentParser(
        description='SOLAR PhotoSync - Webhook Setup Utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Set webhook:    python webhook_setup.py set --url https://your-server.com/api/photosync/webhook
  Get info:       python webhook_setup.py info
  Delete webhook: python webhook_setup.py delete
  Test bot:       python webhook_setup.py test
        """
    )
    
    parser.add_argument(
        'action',
        choices=['set', 'delete', 'info', 'test'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--token', '-t',
        help='Bot token (or use config file)',
        default=None
    )
    
    parser.add_argument(
        '--url', '-u',
        help='Webhook URL (for set action)',
        default=None
    )
    
    parser.add_argument(
        '--secret', '-s',
        help='Webhook secret token',
        default=None
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Path to config file',
        default=None
    )
    
    args = parser.parse_args()
    
    # Загружаем токен из конфига или аргумента
    token = args.token
    webhook_url = args.url
    secret = args.secret
    
    if not token:
        try:
            config = load_config(args.config)
            token = config.get("bot", {}).get("token")
            
            if not webhook_url:
                webhook_url = config.get("bot", {}).get("webhook_url")
            
            if not secret:
                secret = config.get("bot", {}).get("webhook_secret")
                
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Please provide --token argument")
            sys.exit(1)
    
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("Error: Bot token not configured!")
        print("Please set token in config file or use --token argument")
        sys.exit(1)
    
    print("=" * 50)
    print("☀️  SOLAR PhotoSync - Webhook Setup")
    print("=" * 50)
    print()
    
    if args.action == 'test':
        print("Testing bot connection...")
        result = get_me(token)
        
        if result.get("ok"):
            bot_info = result["result"]
            print(f"✅ Bot connected successfully!")
            print(f"   Name: {bot_info.get('first_name')}")
            print(f"   Username: @{bot_info.get('username')}")
            print(f"   Bot ID: {bot_info.get('id')}")
        else:
            print(f"❌ Error: {result.get('description')}")
    
    elif args.action == 'info':
        print("Getting webhook info...")
        result = get_webhook_info(token)
        
        if result.get("ok"):
            info = result["result"]
            print(f"Webhook URL: {info.get('url') or 'Not set'}")
            print(f"Pending updates: {info.get('pending_update_count', 0)}")
            print(f"Last error: {info.get('last_error_message', 'None')}")
            
            if info.get('last_error_date'):
                from datetime import datetime
                error_date = datetime.fromtimestamp(info['last_error_date'])
                print(f"Last error date: {error_date}")
        else:
            print(f"❌ Error: {result.get('description')}")
    
    elif args.action == 'set':
        if not webhook_url:
            print("Error: Webhook URL required!")
            print("Use --url argument or set in config file")
            sys.exit(1)
        
        print(f"Setting webhook to: {webhook_url}")
        result = set_webhook(token, webhook_url, secret)
        
        if result.get("ok"):
            print("✅ Webhook set successfully!")
            print()
            print("Now your bot will receive updates at:")
            print(f"  {webhook_url}")
        else:
            print(f"❌ Error: {result.get('description')}")
    
    elif args.action == 'delete':
        print("Deleting webhook...")
        result = delete_webhook(token)
        
        if result.get("ok"):
            print("✅ Webhook deleted successfully!")
        else:
            print(f"❌ Error: {result.get('description')}")
    
    print()


if __name__ == "__main__":
    main()
