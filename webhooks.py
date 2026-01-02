"""Webhook integrations for Slack, Discord, and Teams for StealthCrawler v17."""

import asyncio
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class WebhookNotifier:
    """
    Send notifications to Slack, Discord, and Microsoft Teams.
    
    Features:
    - Slack webhook integration
    - Discord webhook integration
    - Microsoft Teams webhook integration
    - Customizable message formatting
    """
    
    def __init__(
        self,
        slack_url: Optional[str] = None,
        discord_url: Optional[str] = None,
        teams_url: Optional[str] = None
    ):
        self.slack_url = slack_url
        self.discord_url = discord_url
        self.teams_url = teams_url
        
    async def notify_slack(self, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send notification to Slack.
        
        Args:
            message: Message text
            data: Optional additional data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.slack_url:
            return False
        
        try:
            payload = {
                "text": message,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
            }
            
            # Add fields if data provided
            if data:
                fields = []
                for key, value in data.items():
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*{key}:*\n{value}"
                    })
                
                payload["blocks"].append({
                    "type": "section",
                    "fields": fields
                })
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.slack_url, json=payload)
                
                if response.status_code == 200:
                    logger.info("Slack notification sent")
                    return True
                else:
                    logger.error(f"Slack notification failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            return False
    
    async def notify_discord(self, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send notification to Discord.
        
        Args:
            message: Message text
            data: Optional additional data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.discord_url:
            return False
        
        try:
            payload = {
                "content": message,
                "embeds": []
            }
            
            # Add embed if data provided
            if data:
                embed = {
                    "title": "Crawl Details",
                    "fields": []
                }
                
                for key, value in data.items():
                    embed["fields"].append({
                        "name": key,
                        "value": str(value),
                        "inline": True
                    })
                
                payload["embeds"].append(embed)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.discord_url, json=payload)
                
                if response.status_code == 204:
                    logger.info("Discord notification sent")
                    return True
                else:
                    logger.error(f"Discord notification failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Discord notification error: {e}")
            return False
    
    async def notify_teams(self, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send notification to Microsoft Teams.
        
        Args:
            message: Message text
            data: Optional additional data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.teams_url:
            return False
        
        try:
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": "StealthCrawler Notification",
                "themeColor": "0078D7",
                "title": "StealthCrawler v17",
                "text": message,
                "sections": []
            }
            
            # Add facts if data provided
            if data:
                facts = []
                for key, value in data.items():
                    facts.append({
                        "name": key,
                        "value": str(value)
                    })
                
                payload["sections"].append({
                    "facts": facts
                })
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.teams_url, json=payload)
                
                if response.status_code == 200:
                    logger.info("Teams notification sent")
                    return True
                else:
                    logger.error(f"Teams notification failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Teams notification error: {e}")
            return False
    
    async def notify_all(self, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
        """
        Send notification to all configured webhooks.
        
        Args:
            message: Message text
            data: Optional additional data
            
        Returns:
            Dictionary with results for each platform
        """
        results = {}
        
        if self.slack_url:
            results['slack'] = await self.notify_slack(message, data)
        
        if self.discord_url:
            results['discord'] = await self.notify_discord(message, data)
        
        if self.teams_url:
            results['teams'] = await self.notify_teams(message, data)
        
        return results
    
    async def notify_crawl_started(self, start_urls: list, max_depth: int) -> None:
        """Notify that a crawl has started."""
        message = "🚀 Crawl Started"
        data = {
            "Start URLs": ", ".join(start_urls[:3]) + ("..." if len(start_urls) > 3 else ""),
            "Max Depth": max_depth,
            "URL Count": len(start_urls)
        }
        await self.notify_all(message, data)
    
    async def notify_crawl_completed(self, visited: int, success: int, errors: int, duration: float) -> None:
        """Notify that a crawl has completed."""
        message = "✅ Crawl Completed"
        data = {
            "Visited URLs": visited,
            "Successful": success,
            "Errors": errors,
            "Success Rate": f"{(success / visited * 100) if visited > 0 else 0:.1f}%",
            "Duration": f"{duration:.1f}s"
        }
        await self.notify_all(message, data)
    
    async def notify_error(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Notify about an error."""
        message = f"❌ Error: {error_message}"
        await self.notify_all(message, context)
