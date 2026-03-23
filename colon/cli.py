"""
Colonees Command Line Interface
"""

import asyncio
import argparse
import json
import logging
from typing import Dict, Any

from .core import ColoneesPlatform


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def invoke_command(args):
    """Invoke the platform with a goal"""
    platform = ColoneesPlatform()

    try:
        print("Initializing Colonees Platform...")
        await platform.initialize()

        print(f"Processing goal: {args.goal}")
        result = await platform.handle_request(
            user_goal=args.goal,
            context={'user_id': args.user_id or 'cli_user'}
        )

        print(f"Status: {result['status']}")
        print(f"Response: {result['response']}")

        if result.get('final_asset'):
            print(f"Asset: {result['final_asset']}")

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to: {args.output}")

    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        await platform.shutdown()

    return 0


async def platform_status_command(args):
    """Get platform status command"""
    platform = ColoneesPlatform()

    try:
        print("Initializing Colonees Platform...")
        await platform.initialize()

        status = await platform.get_platform_status()

        print("Colonees Platform Status:")
        print(f"  Initialized: {status['platform_initialized']}")
        print(f"  Active Sessions: {status['active_sessions']}")
        print(f"  Total Sessions Created: {status['metrics']['total_sessions_created']}")
        print(f"  Active Users: {status['metrics']['active_users']}")
        print(f"  Max Concurrent Users: {status['config_summary']['max_concurrent_users']}")

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(status, f, indent=2)
            print(f"Status saved to: {args.output}")

    except Exception as e:
        print(f"Error getting platform status: {e}")
        return 1
    finally:
        await platform.shutdown()

    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Colonees — The Autonomous Agent Swarm Platform",
        epilog="Open-source, production-grade autonomous agent swarm platform."
    )
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Invoke command
    invoke_parser = subparsers.add_parser("invoke", help="Invoke the platform with a goal")
    invoke_parser.add_argument("--goal", required=True, help="The goal or task to accomplish")
    invoke_parser.add_argument("--user-id", help="User identifier")
    invoke_parser.add_argument("--output", help="Output file for results")

    # Platform status command
    status_parser = subparsers.add_parser("status", help="Get platform status")
    status_parser.add_argument("--output", help="Output file for status")

    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.command == "invoke":
        return asyncio.run(invoke_command(args))
    elif args.command == "status":
        return asyncio.run(platform_status_command(args))
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit(main())
