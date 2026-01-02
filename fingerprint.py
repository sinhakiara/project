"""Browser fingerprint randomization for StealthCrawler v17."""

import random
from typing import Dict, List


class FingerprintRandomizer:
    """
    Randomize browser fingerprints to avoid detection.
    
    Features:
    - User agent rotation
    - Screen resolution randomization
    - Timezone randomization
    - Language randomization
    """
    
    USER_AGENTS = [
        # Chrome on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        # Chrome on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        # Firefox on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        # Firefox on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        # Safari on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        # Edge on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    ]
    
    SCREEN_RESOLUTIONS = [
        (1920, 1080),
        (1366, 768),
        (1536, 864),
        (1440, 900),
        (1280, 720),
        (2560, 1440),
    ]
    
    TIMEZONES = [
        'America/New_York',
        'America/Los_Angeles',
        'America/Chicago',
        'Europe/London',
        'Europe/Paris',
        'Asia/Tokyo',
        'Australia/Sydney',
    ]
    
    LANGUAGES = [
        'en-US',
        'en-GB',
        'en-CA',
        'en-AU',
        'fr-FR',
        'de-DE',
        'es-ES',
    ]
    
    def get_user_agent(self) -> str:
        """Get a random user agent."""
        return random.choice(self.USER_AGENTS)
    
    def get_viewport(self) -> Dict[str, int]:
        """Get a random viewport size."""
        width, height = random.choice(self.SCREEN_RESOLUTIONS)
        return {'width': width, 'height': height}
    
    def get_timezone(self) -> str:
        """Get a random timezone."""
        return random.choice(self.TIMEZONES)
    
    def get_language(self) -> str:
        """Get a random language."""
        return random.choice(self.LANGUAGES)
    
    def get_random_fingerprint(self) -> Dict:
        """Get a complete random fingerprint."""
        return {
            'user_agent': self.get_user_agent(),
            'viewport': self.get_viewport(),
            'timezone': self.get_timezone(),
            'language': self.get_language(),
        }
