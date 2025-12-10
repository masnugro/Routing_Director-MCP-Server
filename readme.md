## Connecting HPE Networking Routing Director with MCP
```
Imagine if you can interact with your Transport SDN automation (Routing Director) with natural language, wouldn't it be cool?
This tools could just do that and the response will be user-friendly and easily readable. Not only you can get the information, but you can also create something directly to your Routing Director by asking the Agentic AI.
```

```
Step-by-step guide:
better to run this in virtual environment.
I'm running this in .venv in Macbook

1/pip install -r requirements.txt
2/pip install --upgrade pip
3/uv pip install fastmcp
4/fastmcp install claude-desktop rd_mcp2.py

Available tools:
1/ `get` running active assurance
2/ get customers
3/ get bgp status
4/ get bgp peers number
5/ get cluster health
6/ acknowledge alarm
7/ create new customer
8/ get sites list
9/ get device inventory
10/ get organisation alarms
11/ get alerts
12/ get device series
13/ get topology
14/ get topology nodes
15/ create TE LSP
16/ get TE LSP in networks
17/ delete TE LSP
18/ get TE LSP history
```

## Sample Output

<img width="796" height="891" alt="image" src="https://github.com/user-attachments/assets/eb487fd8-1d3c-4ad0-a286-aed21cd2d1da" />

<img width="843" height="914" alt="image" src="https://github.com/user-attachments/assets/d3dc144c-24bd-4ea8-bb2d-9cbac3821c32" />

# Disclaimer
```
The available function tools (rd_mcp.py) is a living documentation, I will try to add the capabilities along the time.
```
