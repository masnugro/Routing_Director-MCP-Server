## Connecting HPE Networking Routing Director with MCP

Imagine if you can interact with your Transport SDN automation (Routing Director) with natural language, wouldn't it be cool?
This tools could just do that and the response will be user-friendly and easily readable. Not only you can get the information, but you can also create something directly to your Routing Director by asking the Agentic AI.



## Step-by-step guide:
better to run this in virtual environment.
I'm running this using Macbook in .venv

1/pip install -r [requirements.txt](https://github.com/masnugro/Routing_Director-MCP-Server/blob/main/requirements.txt)
2/pip install --upgrade pip
3/uv pip install fastmcp
4/fastmcp install claude-desktop rd_mcp2.py

Available tools:
* ```get``` running active assurance
* ```get``` customers
* ```get``` bgp status
* ```get``` bgp peers number
* ```get``` cluster health
* ```acknowledge``` alarm
* ```create``` new customer
* ```get``` sites list
* ```get``` device inventory
* ```get``` organisation alarms
* ```get``` alerts
* ```get``` device series
* ```get``` topology
* ```get``` topology nodes
* ```create``` TE LSP
* ```get``` TE LSP in networks
* ```delete``` TE LSP
* ```get``` TE LSP history


## Sample Output

<img width="796" height="891" alt="image" src="https://github.com/user-attachments/assets/eb487fd8-1d3c-4ad0-a286-aed21cd2d1da" />

<img width="843" height="914" alt="image" src="https://github.com/user-attachments/assets/d3dc144c-24bd-4ea8-bb2d-9cbac3821c32" />

<img width="755" height="729" alt="image" src="https://github.com/user-attachments/assets/e75ab571-bcc1-4563-9ff2-a7eda23341fe" />


# Disclaimer

The available function tools [rd_mcp.py](https://github.com/masnugro/Routing_Director-MCP-Server/blob/main/rd_mcp.py) is a living documentation, I will try to add the capabilities along the time.

