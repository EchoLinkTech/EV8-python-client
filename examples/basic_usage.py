#!/usr/bin/env python3
"""
Example script demonstrating how to use the EchoLink API Client.
"""
import asyncio
from echolink_client import EchoLinkClient
from rich.console import Console

console = Console()

async def main():
    """Main function demonstrating client usage"""
    console.print("[bold]EchoLink API Client Demo[/bold]")
    console.print("[yellow]Connecting to API...[/yellow]")
    
    # Create client
    async with EchoLinkClient() as client:
        # Check API health
        console.print("[bold]Checking API health:[/bold]")
        health = await client.get_health()
        console.print(health)
        
        # Check balance
        console.print("\n[bold]Checking balance:[/bold]")
        balance = await client.get_balance()
        console.print(balance)
        
        # Get configuration
        console.print("\n[bold]Getting API configuration:[/bold]")
        config = await client.get_config()
        console.print(config)
        
        # Simple chat example
        console.print("\n[bold]Sending a test message:[/bold]")
        response = await client.send_message("Hello! What can you help me with today?")
        console.print(response)
        
        # Start interactive chat
        console.print("\n[bold]Starting interactive chat session:[/bold]")
        console.print("[dim]Type 'exit' to end the session[/dim]")
        
        while True:
            message = input("\nYou: ")
            if message.lower() in ('exit', 'quit'):
                break
                
            result = await client.send_message(message)
            
            if "error" in result:
                console.print(f"\n[red]Error: {result['error']}[/red]")
            else:
                console.print(f"\nAgent: {result.get('response', 'No response')}")
        
        console.print("\n[green]Chat session ended[/green]")

if __name__ == "__main__":
    asyncio.run(main())
