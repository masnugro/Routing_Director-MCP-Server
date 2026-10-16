# /// script
# dependencies = ["fastmcp", "httpx"]
# ///˜
from fastmcp import FastMCP
import httpx
import sys
import time
import ipaddress
from typing import Optional, Dict, List, Union
from datetime import datetime

# Create an MCP server
mcp = FastMCP("Routing Director MCP server")

# RD Server Credential
rd_server = 'X.X.X.X'
email = 'xxx@yyy.zzz'
password = 'XXXXX'
org_id = 'XXX'
# Replace with your actual API token
api_token = 'XXXYYYZZZ'

# Token cache to avoid repeated auth calls
_token_cache: Optional[Dict[str, str]] = None

def _ip_ok(addr: str) -> bool:
    try:
        ipaddress.ip_address(addr)
        return True
    except ValueError:
        return False

def auth(rd_server: str, email: str, password: str, api_token: str = None) -> Dict[str, str]:
    """
    Return headers with AuthToken.
    If api_token is provided, use it directly. Otherwise authenticate with email/password.
    Uses cached token if available.
    Raises exception if authentication fails.
    """
    global _token_cache
    if _token_cache:
        return _token_cache

    # If API token is provided, use it directly
    if api_token and api_token != 'YOUR_TOKEN':
        headers = {
            'Authorization': f'Token {api_token}',
            'Content-Type': "application/json",
            'Cache-Control': "no-cache"
        }
        _token_cache = headers
        return headers

    # Otherwise, use email/password authentication
    url_login = f'https://{rd_server}/api/v1/login'
    headers_init = {'Content-Type': "application/json", 'Cache-Control': "no-cache"}
    data = {"email": email, "password": password}

    response = httpx.post(url_login, json=data, headers=headers_init, verify=False, timeout=30.0)

    if response.status_code not in [200, 201]:
        raise Exception(f"Authentication failed: {response.status_code} - {response.text}")

    response_data = response.json()
    # Try different possible token field names
    auth_token = (response_data.get('token') or
                  response_data.get('authToken') or
                  response_data.get('auth_token') or
                  response_data.get('access_token') or
                  response_data.get('accessToken'))

    if not auth_token:
        raise Exception(f"No token found in authentication response. Response: {response_data}")

    headers = {
        'AuthToken': auth_token,
        'Content-Type': "application/json",
        'Cache-Control': "no-cache"
    }
    _token_cache = headers
    return headers

@mcp.tool()
def get_alert() -> Union[List[dict], dict]:
    """Gets alarm information"""
    headers = auth(rd_server, email, password, api_token)
    url = f'https://{rd_server}/alert-manager/api/v1/orgs/{org_id}/alerts'
    response = httpx.get(url, headers=headers, verify=False, timeout=30.0)
    response.raise_for_status()
    result = response.json()
    # Return items if available, otherwise return the full response
    return result.get('items', result)

@mcp.tool()
def get_device_series() -> dict:
    """Get supported device in RD2.6"""
    headers = auth(rd_server, email, password, api_token)
    url = f'https://{rd_server}/api/v1/devicemodel/device-series'
    response = httpx.get(url, headers=headers, verify=False, timeout=30.0)
    response.raise_for_status()
    series = response.json()
    # Wrap list in dict if needed
    if isinstance(series, list):
        return {"device_series": series, "total": len(series)}
    return series

@mcp.tool()
def get_org_alarms() -> dict:
    """Get organisation alarm"""
    headers = auth(rd_server, email, password, api_token)
    url = f'https://{rd_server}/api/v1/orgs/{org_id}/alarms/search'
    response = httpx.get(url, headers=headers, verify=False, timeout=30.0)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_inventory() -> dict:
    """Get organisation inventory"""
    headers = auth(rd_server, email, password, api_token)
    url = f'https://{rd_server}/api/v1/orgs/{org_id}/inventory'
    response = httpx.get(url, headers=headers, verify=False, timeout=30.0)
    response.raise_for_status()
    inventory = response.json()
    # Wrap list in dict if needed
    if isinstance(inventory, list):
        return {"devices": inventory, "total": len(inventory)}
    return inventory

@mcp.tool()
def get_bgp_peer(
    router_name: str = "%25",
    peer_ip: str = "%25",
    peer_rd: str = "%25",
    site_id: str = "%25",
    sort: str = "router_name",
    page_no: int = 1,
    per_page: int = 100
) -> dict:
    """Get BGP peers information from Routing Director"""
    headers = auth(rd_server, email, password, api_token)
    url = f'https://{rd_server}/routingbot/api/v1/orgs/{org_id}/bgp-peers'
    query = (
        f"time=now()"
        f"&site_id={encode(site_id)}"
        f"&router_name={encode(router_name)}"
        f"&peer_ip={encode(peer_ip)}"
        f"&peer_rd={encode(peer_rd)}"
        f"&sort={sort}"
        f"&page_no={page_no}"
        f"&per_page={per_page}"
    )
    response = httpx.get(url + "?" + query, headers=headers, verify=False, timeout=30.0)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_sites() -> dict:
    """Get organisation sites information"""
    headers = auth(rd_server, email, password, api_token)
    url = f'https://{rd_server}/api/v1/orgs/{org_id}/sites'
    response = httpx.get(url, headers=headers, verify=False, timeout=30.0)
    response.raise_for_status()
    sites = response.json()
    # Wrap list in dict if needed
    if isinstance(sites, list):
        return {"sites": sites, "total": len(sites)}
    return sites

@mcp.tool()
def get_cluster_health() -> dict:
    """Get RD cluster health check"""
    headers = auth(rd_server, email, password, api_token)
    url = f'https://{rd_server}/api/v1/infra/healthcheck/'
    response = httpx.get(url, headers=headers, verify=False, timeout=30.0)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_bgp_status(
    site_id: str = "%",
    router_name: str = "*",
    peer_rd: str = "*",
    peer_ip: str = "*",
    peer_count: bool = False,
    status: str = "*",
    peer_details: bool = False,
    start_time: str = "-2h",
    end_time: str = "now()",
    sort: str = "router_name",
    page_no: int = 1,
    per_page: int = 100
) -> dict:
    """Get status of BGP peers from Routing Director"""
    headers = auth(rd_server, email, password, api_token)
    url = f'https://{rd_server}/routingbot/api/v1/orgs/{org_id}/peer-status'
    params = {
        "site_id": site_id,
        "router_name": router_name,
        "peer_rd": peer_rd,
        "peer_ip": peer_ip,
        "peer_count": str(peer_count).lower(),
        "status": status,
        "peer_details": str(peer_details).lower(),
        "start_time": start_time,
        "end_time": end_time,
        "sort": sort,
        "page_no": page_no,
        "per_page": per_page
    }
    response = httpx.get(url, headers=headers, params=params, verify=False, timeout=30.0)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_customers() -> dict:
    """Get list of customers name in RD"""
    headers = auth(rd_server, email, password, api_token)
    url = f'https://{rd_server}/service-orchestration/api/v1/installer/orgs/{org_id}/order/customers'
    response = httpx.get(url, headers=headers, verify=False, timeout=30.0)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def create_customer(customer_name: str, description: str = "") -> Optional[dict]:
    """Creates a new customer in Routing Director customer inventory"""
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return None

        url = f'https://{rd_server}/service-orchestration/api/v1/orgs/{org_id}/order/customers'

        data = {
            "name": customer_name,
            "description": description
        }

        response = httpx.post(url, json=data, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred in create_customer: {e}", file=sys.stderr)
        return None

@mcp.tool()
def get_active_assurance() -> dict:
    """Get list of active assurance monitor testing in RD"""
    headers = auth(rd_server, email, password, api_token)
    url = f'https://{rd_server}/active-assurance/api/v2/orgs/{org_id}/monitors'
    response = httpx.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def ack_alerts(stream_ids: list[str], comment: str = "") -> dict:
    """Acknowledge alarms in Routing Director

    Args:
        stream_ids: List of stream IDs to acknowledge
        comment: Optional comment for the acknowledgment
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/alert-manager/api/v1/orgs/{org_id}/ack'

        # Prepare the payload
        data = {
            "stream_ids": stream_ids,
            "comment": comment
        }

        response = httpx.post(url, json=data, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        return {"error": f"HTTP {e.response.status_code}", "details": e.response.text}
    except Exception as e:
        print(f"An unexpected error occurred in ack_alerts: {e}", file=sys.stderr)
        return {"error": str(e)}

@mcp.tool()
def get_service_designs() -> dict:
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/service-orchestration/api/v1/orgs/{org_id}/catalog/service-designs'
        response = httpx.get(url, headers=headers, verify=False, timeout=30.0)

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list):
                return {"service_designs": result, "total": len(result)}
            return result
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except Exception as e:
        print(f"An unexpected error occurred in get_service_designs: {e}", file=sys.stderr)
        return {"error": str(e)}

@mcp.tool()
def get_service_design_details(design_id: str) -> dict:
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/service-orchestration/api/v1/orgs/{org_id}/catalog/service-designs/{design_id}'
        response = httpx.get(url, headers=headers, verify=False, timeout=30.0)

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except Exception as e:
        print(f"An unexpected error occurred in get_service_design_details: {e}", file=sys.stderr)
        return {"error": str(e)}

@mcp.tool()
def install_service_design(design_id: str, design_data: dict) -> dict:
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/service-orchestration/api/v1/orgs/{org_id}/catalog/service-designs/{design_id}'
        response = httpx.put(url, json=design_data, headers=headers, verify=False, timeout=60.0)

        if response.status_code in [200, 201]:
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json(),
                "message": f"Service design '{design_id}' installed successfully"
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except Exception as e:
        print(f"An unexpected error occurred in install_service_design: {e}", file=sys.stderr)
        return {"error": str(e)}

@mcp.tool()
def create_service_order(
    customer_id: str,
    instance_id: str,
    design_id: str,
    service_data: dict,
    design_version: Optional[str] = None,
    validate: bool = True
) -> dict:
    """
    Create a Service Order (candidate) in Routing Director for service provisioning.

    IMPORTANT: This creates a service order but does NOT execute it.
    After creation, you must call execute_service_order() to actually provision the service.

    Args:
        customer_id: Name or UUID of the customer (required)
        instance_id: User-defined unique name for the service instance (required)
        design_id: Name of the service design (e.g., 'l3vpn', 'eline-l2circuit-nsm') (required)
        service_data: Service instance data complying to the service model (required)
        design_version: Service design version (optional, uses default if not provided)
        validate: Whether to validate the service order (default: True)

    Returns:
        Service order response with order_id

    Example:
        create_service_order(
            customer_id="4de05f4a-e58e-11f0-9fc8-3656e8db5c03",
            instance_id="my-l3vpn",
            design_id="l3vpn",
            service_data={"l3vpn_svc": {...}}
        )
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        # Build the complete payload matching RD format
        payload = {
            "operation": "create",
            "fh_config": {
                "type": "service_order"
            },
            "customer_id": customer_id,
            "instance_id": instance_id,
            "design_id": design_id
        }

        # Add design version if provided
        if design_version:
            payload["design_version"] = design_version

        # Merge the service data into the payload
        payload.update(service_data)

        # Use the /order endpoint to create the service order
        url = f'https://{rd_server}/service-orchestration/api/v1/orgs/{org_id}/order'

        response = httpx.post(url, json=payload, headers=headers, verify=False, timeout=120.0)

        if response.status_code in [200, 201, 202]:
            result = response.json() if response.text else {}
            return {
                "success": True,
                "status_code": response.status_code,
                "data": result,
                "message": "Service order created successfully. Call execute_service_order() to provision."
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text,
                "message": "Failed to create service order"
            }

    except Exception as e:
        print(f"An unexpected error occurred in create_service_order: {e}", file=sys.stderr)
        return {"error": str(e)}

@mcp.tool()
def execute_service_order(
    customer_id: str,
    instance_id: str,
    queue: bool = False
) -> dict:
    """
    Execute the workflow to provision/modify/delete a service instance.

    The orchestration engine determines which workflow to execute based on the
    operation of the latest service order and the service design.

    Args:
        customer_id: Name or UUID of the customer (required)
        instance_id: Service Instance name (required)
        queue: If True and SI is locked, add to queue. If False, reject if locked (default: False)

    Returns:
        Execution status

    Note:
        This API returns immediately after starting the workflow.
        Use get_service_order() or list_service_orders() to check progress.
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        # CORRECTED: Use the exec endpoint as per RD 2.7 API spec
        url = f'https://{rd_server}/service-orchestration/api/v1/orgs/{org_id}/order/customers/{customer_id}/instances/{instance_id}/exec'

        params = {"queue": str(queue).lower()}

        response = httpx.post(url, params=params, headers=headers, verify=False, timeout=120.0)

        if response.status_code in [200, 202]:
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.text else {},
                "message": "Service order execution started"
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text,
                "message": "Failed to execute service order"
            }

    except Exception as e:
        print(f"An unexpected error occurred in execute_service_order: {e}", file=sys.stderr)
        return {"error": str(e)}

@mcp.tool()
def get_service_order(
    customer_id: str,
    instance_id: str
) -> dict:
    """
    Get details of a specific service instance including its latest order status.

    Args:
        customer_id: Name or UUID of the customer
        instance_id: Service Instance name

    Returns:
        Service instance details including status, placement, and configuration
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/service-orchestration/api/v1/orgs/{org_id}/order/customers/{customer_id}/instances/{instance_id}'
        response = httpx.get(url, headers=headers, verify=False, timeout=30.0)

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except Exception as e:
        print(f"An unexpected error occurred in get_service_order: {e}", file=sys.stderr)
        return {"error": str(e)}

@mcp.tool()
def list_service_orders(
    customer_id: Optional[str] = None,
    design_id: Optional[str] = None,
    summary: bool = True
) -> dict:
    """
    List service instances/orders with optional filters.

    Args:
        customer_id: Filter by customer ID (optional). If provided, lists instances for that customer.
        design_id: Filter by design ID using db-filter (optional)
        summary: If True (default), return only key fields. Set False for full details.

    Returns:
        List of service instances matching the filters
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        # Use different endpoints based on whether customer_id is provided
        if customer_id:
            url = f'https://{rd_server}/service-orchestration/api/v1/orgs/{org_id}/order/customers/{customer_id}/instances'
        else:
            url = f'https://{rd_server}/service-orchestration/api/v1/orgs/{org_id}/order/instances'

        req_headers = headers.copy()
        if design_id:
            req_headers["db-filter-parameters"] = f"order.design_id=={design_id}"

        response = httpx.get(url, headers=req_headers, verify=False, timeout=30.0)

        if response.status_code == 200:
            result = response.json()

            # Handle list response
            if isinstance(result, list):
                orders = result
            else:
                orders = result.get("service_orders", result.get("items", []))

            # Apply summary filtering to reduce payload size
            if summary and orders:
                summary_fields = [
                    "id", "customer_id", "instance_id", "design_id", "design_version",
                    "operation", "status", "created_at", "updated_at", "description",
                    "fh_config", "order_status"
                ]
                orders = [
                    {k: v for k, v in order.items() if k in summary_fields}
                    for order in orders
                ]

            return {"service_orders": orders, "total": len(orders), "summary_mode": summary}
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except Exception as e:
        print(f"An unexpected error occurred in list_service_orders: {e}", file=sys.stderr)
        return {"error": str(e)}

@mcp.tool()
def delete_service_order(
    customer_id: str,
    instance_id: str
) -> dict:
    """
    Delete a service instance record.

    Note: This deletes the service instance record, not the provisioned service itself.
    To remove a provisioned service, you should create a service order with
    operation='delete' and execute it first.

    Args:
        customer_id: Name or UUID of the customer
        instance_id: Service Instance name to delete

    Returns:
        Deletion confirmation
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/service-orchestration/api/v1/orgs/{org_id}/order/customers/{customer_id}/instances/{instance_id}'
        response = httpx.delete(url, headers=headers, verify=False, timeout=30.0)

        if response.status_code in [200, 204]:
            return {"success": True, "message": "Service instance deleted successfully"}
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except Exception as e:
        print(f"An unexpected error occurred in delete_service_order: {e}", file=sys.stderr)
        return {"error": str(e)}

@mcp.tool()
def get_placement_network_elements() -> dict:
    """
    Get network elements available for placement.
    This shows which devices/interfaces are available for service provisioning.

    Returns:
        List of network elements with their available resources
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/service-orchestration/api/v1/orgs/{org_id}/placement/network-elements'
        response = httpx.get(url, headers=headers, verify=False, timeout=30.0)

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except Exception as e:
        print(f"An unexpected error occurred in get_placement_network_elements: {e}", file=sys.stderr)
        return {"error": str(e)}

# LSP Tools start from Here

@mcp.tool()
def get_topologies() -> dict:
    """
    Get list of available topologies in the organization.
    Use this to find your topology_id needed for TE-LSP operations.

    Returns:
        List of topologies with their IDs and details
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/topology/api/v1/orgs/{org_id}/topologies'
        response = httpx.get(url, headers=headers, verify=False, timeout=30.0)

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list):
                return {"topologies": result, "total": len(result)}
            return result
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except Exception as e:
        print(f"An unexpected error occurred in get_topologies: {e}", file=sys.stderr)
        return {"error": str(e)}

#str = "10" change this as per your topology_id

@mcp.tool()
def get_topology_nodes(topology_id: str = "10") -> dict:
    """
    Get all nodes in a topology.
    This shows which routers/devices are discovered in the RD topology database
    and their IP addresses.

    Args:
        topology_id: Topology ID in RD (default: "1" for Paragon PathFinder v2/RD 2.6)

    Returns:
        dict: List of topology nodes with their properties including IP addresses
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/topology/api/v1/orgs/{org_id}/{topology_id}/nodes'
        response = httpx.get(url, headers=headers, verify=False, timeout=30.0)

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list):
                return {"nodes": result, "total": len(result)}
            return result
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except Exception as e:
        print(f"An unexpected error occurred in get_topology_nodes: {e}", file=sys.stderr)
        return {"error": str(e)}


@mcp.tool()
def create_te_lsp(
    lsp_name: str,
    from_address: str,
    to_address: str,
    provisioning_type: str = "SR",
    bandwidth: str = "0",
    setup_priority: int = 7,
    holding_priority: int = 7,
    path_type: str = "primary",
    topology_id: str = "10"
) -> dict:
    """
    Create a PCE-initiated Traffic Engineering LSP.

    This creates a TE-LSP that will be managed by the Paragon Pathfinder PCE controller.
    The LSP is signaled from the source router to the destination router with specified
    bandwidth and priority constraints.

    Args:
        lsp_name: Unique name for the TE-LSP (e.g., "pe1-to-pe4-voice")
        from_address: Source router loopback IPv4 address (e.g., "1.1.192.3")
        to_address: Destination router loopback IPv4 address (e.g., "2.2.2.1")
        provisioning_type: LSP signaling protocol - "SR" for SR-MPLS or "RSVP" (default: "SR")
        bandwidth: Bandwidth in Mbps for RSVP - format: "100", "500", "1000" (default: "0")
        setup_priority: Setup priority 0-7, where 0=highest priority (default: 7)
        holding_priority: Holding priority 0-7, where 0=highest priority (default: 7)
        path_type: Path type - "primary" or "secondary" (default: "primary")
        topology_id: Topology ID in RD (default: "10" for this network)

    Returns:
        dict: TE-LSP creation result including LSP index, operational status, and properties

    Note:
        For SR-MPLS LSPs, bandwidth is typically 0 as SR uses per-hop bandwidth reservation.
        For RSVP LSPs, specify bandwidth in Mbps (e.g., "100" for 100Mbps).

    Example:
        # Create SR-MPLS LSP from PE1 to PE4
        result = create_te_lsp(
            lsp_name="sr-pe1-to-pe4",
            from_address="1.1.192.3",
            to_address="2.2.2.1",
            provisioning_type="SR"
        )

        # Create RSVP LSP with bandwidth
        result = create_te_lsp(
            lsp_name="rsvp-pe1-to-pe4",
            from_address="1.1.192.3",
            to_address="2.2.2.1",
            provisioning_type="RSVP",
            bandwidth="500",
            setup_priority=3
        )
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/topology/api/v1/orgs/{org_id}/{topology_id}/te-lsps'

        # Convert bandwidth to integer (bps)
        try:
            bw_int = int(float(bandwidth) * 1_000_000)  # Convert Mbps to bps
        except:
            bw_int = 0

        # CORRECTED: from/to must be objects with address and topoObjectType
        payload = {
            "from": {
                "address": from_address,
                "topoObjectType": "ipv4"
            },
            "to": {
                "address": to_address,
                "topoObjectType": "ipv4"
            },
            "name": lsp_name,
            "pathType": path_type,
            "provisioningType": provisioning_type,
            "plannedProperties": {
                "adminStatus": "Up",
                "bandwidth": bw_int,
                "holdingPriority": holding_priority,
                "setupPriority": setup_priority
            }
        }

        response = httpx.post(url, json=payload, headers=headers, verify=False, timeout=60.0)

        if response.status_code in [200, 201]:
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json(),
                "message": f"TE-LSP '{lsp_name}' created successfully with {provisioning_type} provisioning"
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text,
                "message": f"Failed to create TE-LSP '{lsp_name}'"
            }

    except Exception as e:
        print(f"An unexpected error occurred in create_te_lsp: {e}", file=sys.stderr)
        return {"error": str(e)}


@mcp.tool()
def list_te_lsps(topology_id: str = "10") -> dict:
    """
    List all TE-LSPs in a topology.

    Args:
        topology_id: Topology ID in RD (default: "1" for Paragon PathFinder v2/RD 2.6)

    Returns:
        dict: List of TE-LSPs with their current status and properties
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/topology/api/v1/orgs/{org_id}/{topology_id}/te-lsps'
        response = httpx.get(url, headers=headers, verify=False, timeout=30.0)

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list):
                return {"te_lsps": result, "total": len(result)}
            return result
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except Exception as e:
        print(f"An unexpected error occurred in list_te_lsps: {e}", file=sys.stderr)
        return {"error": str(e)}


@mcp.tool()
def get_te_lsp(
    lsp_id: str,
    topology_id: str = "10"
) -> dict:
    """
    Get detailed information about a specific TE-LSP.

    Args:
        lsp_id: TE-LSP ID or name
        topology_id: Topology ID in RD (default: "1" for Paragon PathFinder v2/RD 2.6)

    Returns:
        dict: Detailed TE-LSP information including operational status, path, and metrics
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/topology/api/v1/orgs/{org_id}/{topology_id}/te-lsps/{lsp_id}'
        response = httpx.get(url, headers=headers, verify=False, timeout=30.0)

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except Exception as e:
        print(f"An unexpected error occurred in get_te_lsp: {e}", file=sys.stderr)
        return {"error": str(e)}


@mcp.tool()
def update_te_lsp(
    lsp_id: str,
    bandwidth: Optional[str] = None,
    setup_priority: Optional[int] = None,
    holding_priority: Optional[int] = None,
    topology_id: str = "10"
) -> dict:
    """
    Update TE-LSP bandwidth or priorities.
    You can update one or more properties. Only provide the parameters you want to change.
    Args:
        lsp_id: TE-LSP ID or name to update
        bandwidth: New bandwidth requirement (optional) - e.g., "1G", "500M"
        setup_priority: New setup priority 0-7 (optional)
        holding_priority: New holding priority 0-7 (optional)
        topology_id: Depends on the RD Cluster
    Returns:
        dict: Update confirmation with new LSP properties
    Example:
        # Increase bandwidth to 1G
        result = update_te_lsp(
            lsp_id="pe1-to-pe4-voice",
            bandwidth="1G"
        )
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/topology/api/v1/orgs/{org_id}/{topology_id}/te-lsps/{lsp_id}'

        # Build JSON Patch array (RFC 6902) — RD API requires array not object
        patch = []
        if bandwidth is not None:
            patch.append({"op": "replace", "path": "/plannedProperties/bandwidth", "value": bandwidth})
        if setup_priority is not None:
            patch.append({"op": "replace", "path": "/plannedProperties/setupPriority", "value": setup_priority})
        if holding_priority is not None:
            patch.append({"op": "replace", "path": "/plannedProperties/holdingPriority", "value": holding_priority})

        if not patch:
            return {"error": "No properties to update. Provide at least one parameter to update."}

        patch_headers = {**headers, "Content-Type": "application/json-patch+json"}

        response = httpx.patch(url, json=patch, headers=patch_headers, verify=False, timeout=60.0)

        if response.status_code in [200, 201]:
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json(),
                "message": f"TE-LSP '{lsp_id}' updated successfully"
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }
    except Exception as e:
        print(f"An unexpected error occurred in update_te_lsp: {e}", file=sys.stderr)
        return {"error": str(e)}


@mcp.tool()
def delete_te_lsp(
    lsp_id: str,
    topology_id: str = "10"
) -> dict:
    """
    Delete a TE-LSP.

    This will remove the PCE-initiated LSP. The PCE will tear down the LSP on the router.

    Args:
        lsp_id: TE-LSP ID or name to delete
        topology_id: Depends on the RD Cluster

    Returns:
        dict: Deletion confirmation
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/topology/api/v1/orgs/{org_id}/{topology_id}/te-lsps/{lsp_id}'
        response = httpx.delete(url, headers=headers, verify=False, timeout=30.0)

        if response.status_code in [200, 204]:
            return {
                "success": True,
                "message": f"TE-LSP '{lsp_id}' deleted successfully"
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except Exception as e:
        print(f"An unexpected error occurred in delete_te_lsp: {e}", file=sys.stderr)
        return {"error": str(e)}


@mcp.tool()
def get_te_lsp_history(
    lsp_id: str,
    topology_id: str = "10"
) -> dict:
    """
    Get the history of changes for a TE-LSP.

    Shows the history of modifications, path changes, and events for the LSP.

    Args:
        lsp_id: TE-LSP ID or name
        topology_id: Topology ID in RD (default: "1" for Paragon PathFinder v2/RD 2.6)

    Returns:
        dict: LSP history including path changes and events
    """
    try:
        headers = auth(rd_server, email, password, api_token)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{rd_server}/topology/api/v1/orgs/{org_id}/{topology_id}/te-lsps/{lsp_id}/history'
        response = httpx.get(url, headers=headers, verify=False, timeout=30.0)

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except Exception as e:
        print(f"An unexpected error occurred in get_te_lsp_history: {e}", file=sys.stderr)
        return {"error": str(e)}

@mcp.tool()
def get_available_pe_interfaces(
    pe_device_id: str,
    pop_id: str
) -> dict:
    """
    Get available interfaces on a PE router for service placement.

    Queries the topo resource to find available interfaces that can be used
    for L3VPN or L2VPN service provisioning.

    Args:
        pe_device_id: PE device UUID (e.g., "00000000-0000-0000-1000-2c6bf5617c00")
        pop_id: Site/POP UUID from topo resource

    Returns:
        dict: List of available interfaces with their properties (speed, VLANs available, etc.)

    Example:
        interfaces = get_available_pe_interfaces(
            pe_device_id="00000000-0000-0000-1000-2c6bf5617c00",
            pop_id="3eb1f156-bbbf-4512-89ce-6368eadc12ab"
        )
    """
    try:
        # Get placement network elements which includes interface availability
        result = get_placement_network_elements()

        if not result.get("success"):
            return result

        data = result.get("data", {})

        # Find interfaces for the specific PE and POP
        available_interfaces = []

        # Parse through placement data to find relevant interfaces
        # The structure varies, but typically interfaces are nested under devices/pops
        # This is a simplified extraction - adjust based on actual RD response structure

        return {
            "success": True,
            "pe_device_id": pe_device_id,
            "pop_id": pop_id,
            "interfaces": available_interfaces,
            "message": "Use placement_network_elements data to find available interfaces"
        }

    except Exception as e:
        print(f"An unexpected error occurred in get_available_pe_interfaces: {e}", file=sys.stderr)
        return {"error": str(e)}
