#!/usr/bin/env python3
"""
Auto-Update Service for Robot Runner

This service runs in the background and checks for updates periodically.
Can be run as a standalone service or integrated into the main application.

Usage:
    python update_service.py [--interval SECONDS] [--channel stable|beta|canary]

Examples:
    # Check every hour (default)
    python update_service.py

    # Check every 30 minutes
    python update_service.py --interval 1800

    # Use beta channel
    python update_service.py --channel beta
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.updater import AutoUpdater, get_current_version
from shared.config.loader import load_config


def setup_logging():
    """Setup logging for update service"""
    log_dir = Path.home() / "Robot" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "updater.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)


def main():
    """Main entry point for update service"""
    parser = argparse.ArgumentParser(
        description='Auto-Update Service for Robot Runner'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=3600,
        help='Check interval in seconds (default: 3600 = 1 hour)'
    )
    parser.add_argument(
        '--channel',
        choices=['stable', 'beta', 'canary'],
        default='stable',
        help='Update channel (default: stable)'
    )
    parser.add_argument(
        '--repo',
        type=str,
        default='tu-usuario/robotrunner_windows',
        help='GitHub repository (format: owner/repo)'
    )
    parser.add_argument(
        '--check-once',
        action='store_true',
        help='Check once and exit (no loop)'
    )
    parser.add_argument(
        '--version',
        action='store_true',
        help='Show current version and exit'
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging()

    # Show version if requested
    if args.version:
        current_version = get_current_version()
        print(f"Robot Runner v{current_version}")
        return 0

    logger.info("=" * 70)
    logger.info("Auto-Update Service Starting")
    logger.info("=" * 70)
    logger.info(f"Current version: {get_current_version()}")
    logger.info(f"Check interval: {args.interval} seconds")
    logger.info(f"Update channel: {args.channel}")
    logger.info(f"GitHub repo: {args.repo}")

    try:
        # Load config to check if auto-update is enabled
        try:
            config = load_config()
            auto_update_enabled = config.get('auto_update_enabled', True)

            if not auto_update_enabled:
                logger.warning("Auto-update is DISABLED in config.json")
                logger.info("Set 'auto_update_enabled': true to enable")
                return 0

        except Exception as e:
            logger.warning(f"Could not load config: {e}")
            logger.info("Proceeding with default settings")

        # Create updater
        updater = AutoUpdater(
            github_repo=args.repo,
            check_interval=args.interval,
            auto_update=True,
            update_channel=args.channel
        )

        # Check once or run loop
        if args.check_once:
            logger.info("Performing one-time update check...")
            if updater.perform_update():
                logger.info("✅ Update completed successfully")
                return 0
            else:
                logger.info("ℹ️  No updates available or update failed")
                return 1
        else:
            logger.info("Starting update loop...")
            updater.run_update_loop()

    except KeyboardInterrupt:
        logger.info("\n⚠️  Update service stopped by user")
        return 0

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())