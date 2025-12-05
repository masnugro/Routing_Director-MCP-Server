from fastmcp import FastMCP
import httpx
import sys
from typing import Optional, Dict, List, Union

# Create an MCP server
mcp = FastMCP("Routing Director MCP server")

# RD Server Credential
rd_server = 'YOUR_RD_SERVER_IP_ADDRESS'
email = 'EMAIL' # RD is using email as the login credential
password = 'PASSWORD'
org_id = 'YOUR_ORG_ID'
api_token = 'YOUR_API_TOKEN' # Replace with your actual API token

# Token cache to avoid repeated auth calls
_token_cache: Optional[Dict[str, str]] = None

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
    response = httpx.get(url, headers=headers, verify=False)
    response.raise_for_status()
    result = response.json()
    # Return items if available, otherwise return the full response
    return result.get('items', result)

@mcp.tool()
def get_device_series() -> dict:
    """Get supported device in RD2.6"""
    headers = auth(rd_server, email, password, api_token)
    url = f'https://{rd_server}/api/v1/devicemodel/device-series'
    response = httpx.get(url, headers=headers, verify=False)
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
    response = httpx.get(url, headers=headers, verify=False)
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
    response = httpx.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_bgp_peer() -> dict:
    """Get number of BGP peers"""
    headers = auth(rd_server, email, password, api_token)
    url = f'https://{rd_server}/routingbot/api/v1/orgs/{org_id}/bgp-peers'
    response = httpx.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_bgp_status() -> dict:
    """Get status of BGP peers"""
    headers = auth(rd_server, email, password, api_token)
    url = f'https://{rd_server}/routingbot/api/v1/orgs/{org_id}/peer-status'
    response = httpx.get(url, headers=headers, verify=False)
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
