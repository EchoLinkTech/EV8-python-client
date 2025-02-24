# EchoLink API Client

A Python interface for interacting with the EchoLink API service. This client provides easy 
access to all functionality exposed by the API endpoints, including agent creation, chat, 
transaction monitoring, and more.

## Features

- 🔐 **Secure Authentication**: Uses Ethereum wallet signatures for authentication
- 💬 **Interactive Chat**: Communicate with AI agents through an interactive console
- 🤖 **Agent Creation**: Create custom AI agents with specific purposes
- 📊 **Transaction Monitoring**: Track blockchain transactions for agent creation
- 🔄 **Asynchronous API**: Built with modern async/await patterns for responsive interactions
- 🎨 **Rich Console UI**: Beautiful terminal output with color highlighting

## Installation

### Prerequisites

- Python 3.8 or higher
- An Ethereum wallet private key (for authentication)
- The EchoLink API service running (locally or remotely)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/echolink-client.git
   cd echolink-client
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your environment:
   
   Create a `.env` file with your configuration:
   ```
   PRIVATE_KEY=your_ethereum_private_key_here
   ECHOLINK_API_URL=http://localhost:5000
   ```

## Usage

### Interactive Console

The easiest way to use the client is through the interactive console:
```bash
python echolink_client.py --console
```

This launches an interactive shell with commands for all API functions:
```
EchoLink> help
Documented commands (type help <topic>):
========================================
balance        chat           check_agent  check_tx       clear_history
config         create_agent   exit         health         help
history        interactive    quit
```

### API Interface

You can also use the client as a Python library in your own code:
```python
import asyncio
from echolink_client import EchoLinkClient

async def main():
    async with EchoLinkClient() as client:
        # Check API health
        health = await client.get_health()
        print(f"API Status: {health}")
        
        # Chat with an agent
        response = await client.send_message("Hello, how can you help me?")
        print(f"Agent: {response.get('response')}")
        
        # Create a new agent
        result = await client.create_agent_and_wait(
            "Assistant", 
            "Help with programming tasks and technical problems"
        )
        print(f"Agent created: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Command Line Options

The client supports various command-line options:
```
usage: echolink_client.py [-h] [--url URL] [--key KEY] [--env ENV] [--noenv]
                         [--console] [--health] [--balance] [--chat CHAT]
                         [--create CREATE] [--purpose PURPOSE]

EchoLink API Client

options:
  -h, --help           show this help message and exit
  --url URL            API base URL
  --key KEY            Ethereum private key
  --env ENV            Path to .env file
  --noenv              Don't load .env file
  --console            Start interactive console
  --health             Check API health
  --balance            Check balance
  --chat CHAT          Send a chat message
  --create CREATE      Create an agent with the given name
  --purpose PURPOSE    Purpose for agent creation
```

## Authentication

The client uses Ethereum wallet signatures for authentication with the API server. You need to 
provide your private key either:
- In the `.env` file (PRIVATE_KEY=...)
- As a command-line parameter (--key)
- When prompted during runtime

The private key is used to sign authentication messages but is never sent to the server 
directly.

## API Endpoints

The client provides access to all EchoLink API endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/health | Check API health status |
| GET | /api/v1/balance | Get ETH and EKO token balances |
| POST | /api/v1/agents | Create a new AI agent |
| POST | /api/v1/chat | Send a message to the AI agent |
| GET | /api/v1/transactions/{tx_hash} | Check transaction status |
| GET | /api/v1/agent/status | Check agent status |
| GET | /api/v1/config | Get API configuration |

## Error Handling

The client includes comprehensive error handling to manage connection issues, transaction 
failures, and API errors. All responses include appropriate status codes and error messages.

Example error handling:
```python
response = await client.send_message("Hello")
if "error" in response:
    print(f"Error: {response['error']}")
else:
    print(f"Response: {response['response']}")
```

## Example Scripts

See the `examples` directory for sample usage patterns:
- `basic_usage.py` - Simple API interactions
- `interactive_chat.py` - Extended chat session with an AI agent
- `agent_creation.py` - Full agent creation workflow

## Transaction Monitoring

When creating agents or performing other blockchain transactions, the client can monitor and 
wait for confirmation:

```python
# Create agent and wait for confirmation
result = await client.create_agent_and_wait("Assistant", "Purpose description")

# Or manually check a transaction
tx_status = await client.check_transaction("0x123...")
```

## Conversation History

The client maintains a history of chat interactions:

```python
# Get conversation history
history = client.get_conversation_history()

# Clear history
client.clear_conversation_history()
```

## Security Notes

- Never share your private key or commit it to version control
- The client uses secure signature-based authentication rather than storing the key on the 
server
- All API communication should be over HTTPS in production environments
- The private key is only used locally for signing authentication messages

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify your private key is correct
   - Ensure your wallet has sufficient ETH/EKO tokens

2. **Connection Errors**
   - Check if the API server is running
   - Verify the correct URL is configured

3. **Transaction Timeouts**
   - Blockchain transactions may take time, especially on congested networks
   - Increase timeout parameters if needed

### Logging

The client provides detailed logging. To see debug information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
