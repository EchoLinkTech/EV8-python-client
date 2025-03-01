#!/usr/bin/env python3
"""
EV8 AI Agent Framework API Client

A Python interface to interact with the EV8 API service.
This client provides access to all functionality exposed by the API endpoints.
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
import argparse
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from dotenv import load_dotenv
from pathlib import Path
import getpass
import cmd
import readline
import textwrap
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import box

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("echolink_client.log")
    ]
)
logger = logging.getLogger(__name__)

# Rich console for pretty output
console = Console()

class EchoLinkClient:
    """Client for interacting with the EV8 API"""
    
    def __init__(self, base_url: str = None, private_key: str = None, load_env: bool = True):
        """
        Initialize the EV8 API client
        
        Args:
            base_url: API base URL (default: http://localhost:5000)
            private_key: Ethereum private key for authentication
            load_env: Whether to load environment variables from .env
        """
        # Load environment variables if requested
        if load_env:
            env_path = Path('configs/.env')
            if env_path.exists():
                load_dotenv(dotenv_path=env_path)
            else:
                logger.warning(f"Environment file not found at {env_path}")
        
        # Set base URL from argument or environment or default
        self.base_url = base_url or os.environ.get('EV8_API_URL', 'http://localhost:5000')
        
        # Set private key from argument or environment
        self.private_key = private_key or os.environ.get('PRIVATE_KEY')
        
        # Initialize account if private key is available
        self.account = None
        if self.private_key:
            self.account = Account.from_key(self.private_key)
            logger.info(f"Initialized with account address: {self.account.address}")
        
        # Cache for transaction statuses to avoid redundant API calls
        self.tx_cache = {}
        
        # Session for API requests
        self.session = None
        
        # Conversation history
        self.conversation_history = []
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Create authentication headers for API requests
        
        Returns:
            Dict of headers including authentication
        """
        if not self.account:
            logger.error("No private key configured. Authentication will fail.")
            return {}
        
        # Create timestamp for message
        timestamp = int(time.time())
        
        # Create message to sign
        message = f"Authenticate to EchoLink AI: {timestamp}"
        
        # Sign message
        signable_message = encode_defunct(text=message)
        signature = self.account.sign_message(signable_message)
        
        # Return headers
        return {
            "X-Wallet-Signature": signature.signature.hex(),
            "X-Wallet-Address": self.account.address,
            "X-Auth-Timestamp": str(timestamp),
            "Content-Type": "application/json"
        }
    
    async def _make_request(
        self, method: str, endpoint: str, data: Dict = None, 
        auth: bool = True, params: Dict = None
    ) -> Tuple[int, Dict]:
        """
        Make an HTTP request to the API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data
            auth: Whether to include authentication headers
            params: URL parameters
            
        Returns:
            Tuple of (status_code, response_data)
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Create URL
        url = f"{self.base_url}{endpoint}"
        
        # Set headers
        headers = {"Content-Type": "application/json"}
        if auth:
            headers.update(self._get_auth_headers())
        
        try:
            # Make request
            async with self.session.request(
                method, url, json=data, headers=headers, params=params
            ) as response:
                # Parse response
                status = response.status
                try:
                    response_data = await response.json()
                except:
                    response_data = {"error": "Failed to parse response"}
                
                # Return status and data
                return status, response_data
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return 500, {"error": str(e)}
    
    async def get_health(self) -> Dict:
        """
        Check API health status
        
        Returns:
            Health status information
        """
        status, data = await self._make_request("GET", "/api/v1/health", auth=False)
        return data if status == 200 else {"error": data.get("error", "Failed to get health status")}
    
    async def get_balance(self) -> Dict:
        """
        Get ETH and EKO balance
        
        Returns:
            Balance information
        """
        status, data = await self._make_request("GET", "/api/v1/balance")
        return data if status == 200 else {"error": data.get("error", "Failed to get balance")}
    
    async def create_agent(self, name: str, purpose: str) -> Dict:
        """
        Create a new AI agent
        
        Args:
            name: Agent name
            purpose: Agent purpose and capabilities
            
        Returns:
            Transaction information for the agent creation
        """
        # Validate input
        if not name or not purpose:
            return {"error": "Name and purpose are required"}
        
        # Prepare data
        data = {
            "name": name,
            "purpose": purpose
        }
        
        # Make request
        status, response = await self._make_request("POST", "/api/v1/agents", data)
        
        if status == 202:
            return response
        else:
            return {"error": response.get("error", "Failed to create agent")}
    
    async def send_message(self, message: str) -> Dict:
        """
        Send a chat message to the AI agent
        
        Args:
            message: Message text
            
        Returns:
            Agent's response
        """
        # Validate input
        if not message or len(message) > 2000:
            return {"error": "Message must be between 1 and 2000 characters"}
        
        # Prepare data
        data = {
            "message": message
        }
        
        # Make request
        status, response = await self._make_request("POST", "/api/v1/chat", data)
        
        if status == 200:
            # Store in conversation history
            self.conversation_history.append({
                "user": message, 
                "agent": response.get("response", ""),
                "timestamp": datetime.now().isoformat()
            })
            return response
        else:
            return {"error": response.get("error", "Failed to send message")}
    
    async def check_transaction(self, tx_hash: str) -> Dict:
        """
        Check status of a blockchain transaction
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction status
        """
        # Check cache first
        if tx_hash in self.tx_cache and self.tx_cache[tx_hash].get("status") == "confirmed":
            return self.tx_cache[tx_hash]
        
        # Make request
        status, response = await self._make_request(
            "GET", f"/api/v1/transactions/{tx_hash}", auth=False
        )
        
        # Update cache if successful
        if status in (200, 202):
            self.tx_cache[tx_hash] = response
        
        return response
    
    async def check_agent_status(self, agent_address: str) -> Dict:
        """
        Check status of an AI agent
        
        Args:
            agent_address: Agent address
            
        Returns:
            Agent status
        """
        # Make request
        status, response = await self._make_request(
            "GET", "/api/v1/agent/status", params={"address": agent_address}
        )
        
        return response if status == 200 else {"error": response.get("error", "Failed to check agent status")}
    
    async def get_config(self) -> Dict:
        """
        Get API configuration
        
        Returns:
            API configuration
        """
        status, response = await self._make_request("GET", "/api/v1/config", auth=False)
        return response if status == 200 else {"error": response.get("error", "Failed to get API configuration")}
    
    async def wait_for_transaction(self, tx_hash: str, timeout: int = 300) -> Dict:
        """
        Wait for a transaction to be confirmed
        
        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds
            
        Returns:
            Final transaction status
        """
        start_time = time.time()
        
        console.print(f"[yellow]Waiting for transaction confirmation: {tx_hash}[/yellow]")
        
        with console.status("[bold green]Processing transaction...") as status:
            while time.time() - start_time < timeout:
                # Check transaction status
                response = await self.check_transaction(tx_hash)
                
                # If confirmed or failed, return status
                if response.get("status") == "confirmed":
                    console.print("[green]Transaction confirmed![/green]")
                    return response
                elif response.get("status") == "failed":
                    console.print("[red]Transaction failed![/red]")
                    return response
                
                # Wait before retrying
                status.update(f"[bold yellow]Waiting for transaction: {time.time() - start_time:.1f}s elapsed[/bold yellow]")
                await asyncio.sleep(5)
            
            # Timeout
            console.print("[red]Transaction confirmation timeout![/red]")
            return {"error": "Transaction confirmation timed out", "tx_hash": tx_hash}
    
    async def create_agent_and_wait(self, name: str, purpose: str) -> Dict:
        """
        Create an agent and wait for confirmation
        
        Args:
            name: Agent name
            purpose: Agent purpose
            
        Returns:
            Agent creation result
        """
        # Create agent
        result = await self.create_agent(name, purpose)
        
        if "transaction" in result and "id" in result["transaction"]:
            # Wait for transaction confirmation
            tx_result = await self.wait_for_transaction(result["transaction"]["id"])
            result["transaction"]["status"] = tx_result.get("status", "unknown")
            return result
        else:
            return {"error": result.get("error", "Failed to create agent")}
    
    def get_conversation_history(self) -> List[Dict]:
        """
        Get conversation history
        
        Returns:
            List of conversation items
        """
        return self.conversation_history
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")

class AsyncEchoLinkConsole(cmd.Cmd):
    """Interactive command console for EV8 API with asyncio support"""
    
    intro = """
    Welcome to the EV8 API Client Console
    =========================================
    Type 'help' or '?' to list commands.
    Type 'exit' or 'quit' to exit.
    """
    prompt = "EV8> "
    
    def __init__(self, base_url=None, private_key=None):
        """Initialize the console"""
        super().__init__()
        self.client = None
        self.base_url = base_url
        self.private_key = private_key
        self.stopped = False
        
    async def setup(self):
        """Initialize the API client"""
        self.client = EchoLinkClient(self.base_url, self.private_key)
        await self.client.__aenter__()
        
        # Check health to verify connection
        health = await self.client.get_health()
        if "error" in health:
            console.print(f"[red]Failed to connect to API: {health['error']}[/red]")
        else:
            network = health.get("network", "unknown")
            block = health.get("block_height", "unknown")
            provider = health.get("provider", "unknown")
            console.print(f"[green]Connected to EchoLink API[/green]")
            console.print(f"[bold]Network:[/bold] {network}")
            console.print(f"[bold]Block:[/bold] {block}")
            console.print(f"[bold]AI Provider:[/bold] {provider}")
    
    async def async_cmdloop(self):
        """Async version of cmdloop that properly integrates with asyncio"""
        self.preloop()
        try:
            if self.intro:
                console.print(self.intro)
            while not self.stopped:
                try:
                    # Get input in a way that doesn't block the event loop
                    line = await asyncio.get_event_loop().run_in_executor(None, lambda: input(self.prompt))
                    await self.async_onecmd(line)
                except EOFError:
                    self.stopped = True
                    break
        finally:
            self.postloop()
            # Clean up client
            if self.client:
                await self.client.__aexit__(None, None, None)
    
    async def async_onecmd(self, line):
        """Async version of onecmd"""
        cmd, arg, line = self.parseline(line)
        if not line:
            return
        if cmd is None:
            return await self.async_default(line)
        if cmd == '':
            return await self.async_default(line)
        
        try:
            # First, try to find the async version of the command
            func = getattr(self, f'async_do_{cmd}', None)
            if func:
                return await func(arg)
            
            # Fall back to sync version for simple commands
            func = getattr(self, f'do_{cmd}', None)
            if func:
                return func(arg)
            
            return await self.async_default(line)
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
    
    async def async_default(self, line):
        """Default async command handler"""
        if line.strip() == 'EOF':
            self.stopped = True
            return
        console.print(f"[yellow]Unknown command: {line}[/yellow]")
        console.print("Type 'help' for a list of commands.")
    
    async def async_do_health(self, arg):
        """Check API health status"""
        result = await self.client.get_health()
        self._print_result(result)
    
    async def async_do_balance(self, arg):
        """Check ETH and EKO balance"""
        result = await self.client.get_balance()
        
        if "error" in result:
            console.print(f"[red]Error: {result['error']}[/red]")
        else:
            table = Table(title="Account Balance", box=box.ROUNDED)
            table.add_column("Token", style="cyan")
            table.add_column("Balance", style="green")
            table.add_column("Network", style="magenta")
            
            table.add_row(
                "ETH", 
                f"{result.get('ethBalance', 0):.6f}", 
                result.get("network", "unknown")
            )
            table.add_row(
                "EKO", 
                f"{result.get('ekoBalance', 0):.4f}", 
                result.get("network", "unknown")
            )
            
            console.print(table)
    
    async def async_do_create_agent(self, arg):
        """Create a new AI agent"""
        if not arg:
            console.print("[yellow]Usage: create_agent <agent_name>[/yellow]")
            return
        
        name = arg
        console.print("[bold]Enter agent purpose (what should this AI agent help with?):[/bold]")
        console.print("[dim]Press Ctrl+D (or Ctrl+Z on Windows) when finished[/dim]")
        
        lines = []
        try:
            # Get multiline input in a way that works with asyncio
            while True:
                line = await asyncio.get_event_loop().run_in_executor(None, input)
                lines.append(line)
        except EOFError:
            pass
        
        purpose = "\n".join(lines)
        console.print(f"[yellow]Creating agent: {name}[/yellow]")
        
        # Create agent and wait for confirmation
        result = await self.client.create_agent_and_wait(name, purpose)
        self._print_result(result)
    
    async def async_do_chat(self, arg):
        """Send a message to the AI agent"""
        if not arg:
            console.print("[yellow]Usage: chat <message>[/yellow]")
            return
        
        result = await self.client.send_message(arg)
        
        if "error" in result:
            console.print(f"[red]Error: {result['error']}[/red]")
        else:
            response = result.get("response", "No response")
            metadata = result.get("metadata", {})
            
            # Format response with markdown
            md = Markdown(response)
            console.print(Panel(md, title="Agent Response", border_style="green"))
            
            # Print metadata
            if metadata:
                console.print("[dim]Response time:[/dim]", metadata.get("response_time", "unknown"))
                console.print("[dim]Tokens used:[/dim]", metadata.get("tokens_used", "unknown"))
    
    async def async_do_interactive(self, arg):
        """Start interactive chat session with the AI agent"""
        console.print("[bold]Starting interactive chat session[/bold]")
        console.print("[dim]Type 'exit' or press Ctrl+D to end the session[/dim]")
        
        while True:
            try:
                msg = await asyncio.get_event_loop().run_in_executor(None, lambda: input("\nYou: "))
                if msg.lower() in ('exit', 'quit'):
                    break
                
                result = await self.client.send_message(msg)
                
                if "error" in result:
                    console.print(f"\n[red]Error: {result['error']}[/red]")
                else:
                    response = result.get("response", "No response")
                    # Format and print response
                    console.print("\n[bold cyan]Agent:[/bold cyan]", style="cyan")
                    console.print(response)
            except EOFError:
                break
        
        console.print("[yellow]Ending chat session[/yellow]")
    
    async def async_do_check_tx(self, arg):
        """Check status of a transaction"""
        if not arg:
            console.print("[yellow]Usage: check_tx <tx_hash>[/yellow]")
            return
        
        result = await self.client.check_transaction(arg)
        self._print_result(result)
    
    async def async_do_check_agent(self, arg):
        """Check status of an AI agent"""
        if not arg:
            console.print("[yellow]Usage: check_agent <agent_address>[/yellow]")
            return
        
        result = await self.client.check_agent_status(arg)
        self._print_result(result)
    
    async def async_do_config(self, arg):
        """Get API configuration"""
        result = await self.client.get_config()
        self._print_result(result)
    
    async def async_do_history(self, arg):
        """Show conversation history"""
        history = self.client.get_conversation_history()
        
        if not history:
            console.print("[yellow]No conversation history found[/yellow]")
            return
        
        for i, item in enumerate(history, 1):
            console.print(f"\n[bold]--- Message {i} ---[/bold]")
            console.print(f"[bold cyan]You:[/bold cyan] {item['user']}")
            console.print(f"[bold green]Agent:[/bold green] {item['agent']}")
            console.print(f"[dim]Time: {item['timestamp']}[/dim]")
    
    async def async_do_clear_history(self, arg):
        """Clear conversation history"""
        self.client.clear_conversation_history()
        console.print("[green]Conversation history cleared[/green]")
    
    async def async_do_exit(self, arg):
        """Exit the console"""
        console.print("[yellow]Exiting EchoLink console...[/yellow]")
        self.stopped = True
        return True
    
    async def async_do_quit(self, arg):
        """Exit the console"""
        return await self.async_do_exit(arg)
    
    # Compatibility methods for cmd.Cmd
    def do_exit(self, arg):
        """Exit compatibility method"""
        self.stopped = True
        return True
        
    def do_quit(self, arg):
        """Quit compatibility method"""
        self.stopped = True
        return True
    
    def _print_result(self, result):
        """Print result in a formatted way"""
        if isinstance(result, dict):
            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
            else:
                console.print(json.dumps(result, indent=2))
        else:
            console.print(result)

async def console_mode(base_url=None, private_key=None):
    """Run interactive console with proper async handling"""
    console_client = AsyncEchoLinkConsole(base_url, private_key)
    await console_client.setup()
    await console_client.async_cmdloop()

async def main_async():
    """Main async function for command-line interface"""
    parser = argparse.ArgumentParser(description="EchoLink API Client")
    parser.add_argument("--url", help="API base URL", default=None)
    parser.add_argument("--key", help="Ethereum private key", default=None)
    parser.add_argument("--env", help="Path to .env file", default=None)
    parser.add_argument("--noenv", action="store_true", help="Don't load .env file")
    parser.add_argument("--console", action="store_true", help="Start interactive console")
    parser.add_argument("--health", action="store_true", help="Check API health")
    parser.add_argument("--balance", action="store_true", help="Check balance")
    parser.add_argument("--chat", help="Send a chat message")
    parser.add_argument("--create", help="Create an agent with the given name")
    parser.add_argument("--purpose", help="Purpose for agent creation")
    
    args = parser.parse_args()
    
    # Load environment variables
    if args.env and not args.noenv:
        load_dotenv(dotenv_path=args.env)
    
    # Initialize client
    private_key = args.key
    if not private_key and not args.noenv:
        if os.environ.get('PRIVATE_KEY'):
            private_key = os.environ.get('PRIVATE_KEY')
        else:
            console.print("[yellow]No private key provided in arguments or environment[/yellow]")
            private_key = getpass.getpass("Enter private key: ")
    
    # If console mode, start interactive console with proper async handling
    if args.console:
        await console_mode(args.url, private_key)
        return
    
    # Create client for individual commands
    async with EchoLinkClient(args.url, private_key, not args.noenv) as client:
        # Health check
        if args.health:
            result = await client.get_health()
            console.print(json.dumps(result, indent=2))
        
        # Balance check
        if args.balance:
            result = await client.get_balance()
            console.print(json.dumps(result, indent=2))
        
        # Chat
        if args.chat:
            result = await client.send_message(args.chat)
            console.print(json.dumps(result, indent=2))
        
        # Create agent
        if args.create:
            if not args.purpose:
                console.print("[red]Error: --purpose is required for agent creation[/red]")
                return
            
            result = await client.create_agent_and_wait(args.create, args.purpose)
            console.print(json.dumps(result, indent=2))
        
        # If no commands specified and not console mode, show help
        if not any([args.health, args.balance, args.chat, args.create, args.console]):
            parser.print_help()

def main():
    """Main function for command-line interface"""
    try:
        # Run async main
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        logger.exception("Unhandled exception")
    finally:
        console.print("[green]Goodbye![/green]")

if __name__ == "__main__":
    main()
