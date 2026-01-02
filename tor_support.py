"""Tor network support for StealthCrawler v17."""

import asyncio
import logging
from typing import Optional
from stem import Signal
from stem.control import Controller

logger = logging.getLogger(__name__)


class TorSupport:
    """
    Tor network integration for anonymous crawling.
    
    Features:
    - Tor connection management
    - IP rotation
    - Circuit management
    - Connection verification
    """
    
    def __init__(
        self,
        socks_port: int = 9050,
        control_port: int = 9051,
        password: Optional[str] = None
    ):
        self.socks_port = socks_port
        self.control_port = control_port
        self.password = password
        self.controller: Optional[Controller] = None
        
    async def connect(self) -> bool:
        """
        Connect to Tor control port.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            self.controller = Controller.from_port(port=self.control_port)
            self.controller.authenticate(password=self.password)
            logger.info("Connected to Tor control port")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Tor: {e}")
            return False
    
    async def get_new_ip(self) -> bool:
        """
        Request a new Tor circuit (new IP).
        
        Returns:
            True if successful, False otherwise
        """
        if not self.controller:
            logger.error("Not connected to Tor")
            return False
        
        try:
            self.controller.signal(Signal.NEWNYM)
            logger.info("Requested new Tor circuit")
            
            # Wait for new circuit to be established
            await asyncio.sleep(5)
            return True
            
        except Exception as e:
            logger.error(f"Failed to get new IP: {e}")
            return False
    
    async def get_current_ip(self) -> Optional[str]:
        """
        Get current Tor exit IP address.
        
        Returns:
            IP address or None
        """
        try:
            import httpx
            
            proxy_url = f"socks5://127.0.0.1:{self.socks_port}"
            async with httpx.AsyncClient(proxies=proxy_url, timeout=10.0) as client:
                response = await client.get('https://api.ipify.org?format=json')
                data = response.json()
                ip = data.get('ip')
                logger.info(f"Current Tor IP: {ip}")
                return ip
                
        except Exception as e:
            logger.error(f"Failed to get current IP: {e}")
            return None
    
    def get_proxy_settings(self) -> dict:
        """
        Get proxy settings for use with browsers.
        
        Returns:
            Dictionary with proxy configuration
        """
        return {
            'server': f'socks5://127.0.0.1:{self.socks_port}'
        }
    
    async def verify_connection(self) -> bool:
        """
        Verify Tor connection is working.
        
        Returns:
            True if working, False otherwise
        """
        try:
            import httpx
            
            proxy_url = f"socks5://127.0.0.1:{self.socks_port}"
            async with httpx.AsyncClient(proxies=proxy_url, timeout=10.0) as client:
                # Check Tor check page
                response = await client.get('https://check.torproject.org/api/ip')
                data = response.json()
                
                if data.get('IsTor'):
                    logger.info("Tor connection verified")
                    return True
                else:
                    logger.warning("Not using Tor")
                    return False
                    
        except Exception as e:
            logger.error(f"Tor verification failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close Tor connection."""
        if self.controller:
            self.controller.close()
            logger.info("Tor connection closed")
