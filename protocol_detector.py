"""Protocol detection for WebSocket, GraphQL, and SSE for StealthCrawler v17."""

import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ProtocolDetector:
    """
    Detect various web protocols and APIs.
    
    Features:
    - WebSocket detection
    - GraphQL endpoint detection
    - Server-Sent Events (SSE) detection
    - REST API pattern detection
    """
    
    @staticmethod
    def detect_websocket(html: str, url: str) -> Optional[str]:
        """
        Detect WebSocket connections in HTML.
        
        Args:
            html: HTML content
            url: Page URL
            
        Returns:
            WebSocket URL if found, None otherwise
        """
        # Look for WebSocket URL patterns
        ws_patterns = [
            r'ws[s]?://[^\s\'"]+',
            r'new\s+WebSocket\([\'"]([^\'"]+)[\'"]',
        ]
        
        for pattern in ws_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                ws_url = match.group(1) if match.lastindex else match.group(0)
                logger.info(f"WebSocket detected: {ws_url}")
                return ws_url
        
        return None
    
    @staticmethod
    def detect_graphql(html: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Detect GraphQL endpoints.
        
        Args:
            html: HTML content
            url: Page URL
            
        Returns:
            Dictionary with GraphQL info if found, None otherwise
        """
        graphql_indicators = [
            r'/graphql',
            r'\.graphql',
            r'query\s*{',
            r'mutation\s*{',
            r'__typename',
        ]
        
        for indicator in graphql_indicators:
            if re.search(indicator, html, re.IGNORECASE):
                # Try to find endpoint
                endpoint_match = re.search(r'[\'"]([^\'"]*graphql[^\'"]*)[\'"]', html, re.IGNORECASE)
                endpoint = endpoint_match.group(1) if endpoint_match else '/graphql'
                
                logger.info(f"GraphQL detected: {endpoint}")
                return {
                    'endpoint': endpoint,
                    'detected': True
                }
        
        return None
    
    @staticmethod
    def detect_sse(headers: Dict[str, str]) -> bool:
        """
        Detect Server-Sent Events (SSE).
        
        Args:
            headers: Response headers
            
        Returns:
            True if SSE detected, False otherwise
        """
        content_type = headers.get('content-type', '').lower()
        
        if 'text/event-stream' in content_type:
            logger.info("SSE detected")
            return True
        
        return False
    
    @staticmethod
    def detect_rest_api(url: str, html: str) -> Optional[Dict[str, Any]]:
        """
        Detect REST API patterns.
        
        Args:
            url: Page URL
            html: HTML content
            
        Returns:
            Dictionary with API info if found, None otherwise
        """
        api_patterns = [
            r'/api/',
            r'/v\d+/',
            r'\.json',
        ]
        
        for pattern in api_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                logger.info(f"REST API detected in URL: {url}")
                return {
                    'type': 'rest',
                    'url': url,
                    'detected': True
                }
        
        # Check for API documentation links
        api_doc_patterns = [
            r'api[/-]docs?',
            r'swagger',
            r'openapi',
        ]
        
        for pattern in api_doc_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                logger.info(f"API documentation detected")
                return {
                    'type': 'rest',
                    'has_documentation': True,
                    'detected': True
                }
        
        return None
    
    @classmethod
    def detect_all(cls, html: str, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Run all protocol detections.
        
        Args:
            html: HTML content
            url: Page URL
            headers: Response headers
            
        Returns:
            Dictionary with all detected protocols
        """
        return {
            'websocket': cls.detect_websocket(html, url),
            'graphql': cls.detect_graphql(html, url),
            'sse': cls.detect_sse(headers),
            'rest_api': cls.detect_rest_api(url, html),
        }
