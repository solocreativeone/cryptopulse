import httpx
import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NetworkError(Exception):
    """Custom exception for network-related failures."""
    pass

class RateLimitError(NetworkError):
    """Custom exception for 429 Rate Limit hits."""
    pass

class BaseProvider:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.user_agent = "CryptoPulse/0.2.0 (High-Precision CLI Tracker)"

    async def _get(self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Any:
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        req_headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        if headers:
            req_headers.update(headers)
            
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                response = await client.get(url, params=params, headers=req_headers)
                if response.status_code == 429:
                    raise RateLimitError(f"Rate limit hit on {self.__class__.__name__}")
                response.raise_for_status()
                return response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                raise NetworkError(f"API unreachable: {e}")

class CoinGeckoProvider(BaseProvider):
    def __init__(self):
        # Determine if we should use the PRO URL if a key is present
        api_key = os.getenv("CP_COINGECKO_API_KEY")
        default_url = "https://api.coingecko.com/api/v3"
        if api_key and api_key.startswith("CG-"): # Common prefix for Pro keys
             default_url = "https://pro-api.coingecko.com/api/v3"
             
        super().__init__(
            base_url=os.getenv("CP_COINGECKO_BASE_URL", default_url),
            api_key=api_key
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        # Only send the header if we are using the pro-api domain
        if "pro-api.coingecko.com" in self.base_url:
            return {"x-cg-pro-api-key": self.api_key}
        return {}

    async def get_markets(self, per_page: int = 100) -> List[Dict[str, Any]]:
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
            "sparkline": "true"
        }
        return await self._get("coins/markets", params=params, headers=self._get_auth_headers())

    async def get_coin_details(self, coin_id: str) -> Dict[str, Any]:
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "true"
        }
        return await self._get(f"coins/{coin_id}", params=params, headers=self._get_auth_headers())

    async def get_global_data(self) -> Dict[str, Any]:
        return await self._get("global", headers=self._get_auth_headers())

class MobulaProvider(BaseProvider):
    def __init__(self):
        super().__init__(
            base_url=os.getenv("CP_MOBULA_BASE_URL", "https://api.mobula.io/api/1"),
            api_key=os.getenv("CP_MOBULA_API_KEY")
        )

    async def get_markets(self, per_page: int = 100) -> List[Dict[str, Any]]:
        headers = {"Authorization": self.api_key} if self.api_key else None
        data = await self._get("market/data", headers=headers)
        return data.get("data", [])

class CoinPaprikaProvider(BaseProvider):
    def __init__(self):
        super().__init__(
            base_url=os.getenv("CP_COINPAPRIKA_BASE_URL", "https://api.coinpaprika.com/v1")
        )

    async def get_markets(self, per_page: int = 100) -> List[Dict[str, Any]]:
        return await self._get("tickers")

class FiatAPIClient:
    def __init__(self):
        self.base_url = os.getenv("CP_FRANKFURTER_BASE_URL", "https://api.frankfurter.dev/v1")

    async def get_rates(self, base: str = "USD") -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/latest"
        params = {"from": base}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, params=params, headers={"User-Agent": "CryptoPulse/0.2.0"})
                response.raise_for_status()
                return response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                raise NetworkError(f"Fiat Rates API unreachable: {e}")
