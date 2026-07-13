# yahboom-mcp (MCPB Bundle)

SOTA 2026 Yahboom Raspbot v2 ROS 2 MCP Server

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "yahboom-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "yahboom_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **ros_topic_list**: ros_topic_list

## Requirements

- Python 3.12+
- uv
