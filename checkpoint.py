"""Checkpoint and resume system for StealthCrawler v17."""

import json
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manage crawl checkpoints for resume capability.
    
    Features:
    - Save crawl state
    - Load and resume from checkpoint
    - Automatic periodic checkpointing
    - Checkpoint cleanup
    """
    
    def __init__(self, checkpoint_dir: str = 'checkpoints'):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        
    def save(
        self,
        name: str,
        state: Dict[str, Any]
    ) -> bool:
        """
        Save a checkpoint.
        
        Args:
            name: Checkpoint name/identifier
            state: Crawl state to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            checkpoint_file = self.checkpoint_dir / f"{name}.json"
            
            # Add metadata
            state['_metadata'] = {
                'saved_at': datetime.utcnow().isoformat(),
                'name': name
            }
            
            # Save to file
            with open(checkpoint_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            
            logger.info(f"Checkpoint saved: {checkpoint_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False
    
    def load(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a checkpoint.
        
        Args:
            name: Checkpoint name/identifier
            
        Returns:
            Crawl state or None
        """
        try:
            checkpoint_file = self.checkpoint_dir / f"{name}.json"
            
            if not checkpoint_file.exists():
                logger.error(f"Checkpoint not found: {checkpoint_file}")
                return None
            
            with open(checkpoint_file, 'r') as f:
                state = json.load(f)
            
            logger.info(f"Checkpoint loaded: {checkpoint_file}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """
        List all available checkpoints.
        
        Returns:
            List of checkpoint information
        """
        checkpoints = []
        
        try:
            for checkpoint_file in self.checkpoint_dir.glob('*.json'):
                try:
                    with open(checkpoint_file, 'r') as f:
                        state = json.load(f)
                    
                    metadata = state.get('_metadata', {})
                    checkpoints.append({
                        'name': checkpoint_file.stem,
                        'file': str(checkpoint_file),
                        'saved_at': metadata.get('saved_at'),
                        'size': checkpoint_file.stat().st_size
                    })
                except Exception as e:
                    logger.warning(f"Failed to read checkpoint {checkpoint_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
        
        return sorted(checkpoints, key=lambda x: x.get('saved_at', ''), reverse=True)
    
    def delete(self, name: str) -> bool:
        """
        Delete a checkpoint.
        
        Args:
            name: Checkpoint name/identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            checkpoint_file = self.checkpoint_dir / f"{name}.json"
            
            if checkpoint_file.exists():
                checkpoint_file.unlink()
                logger.info(f"Checkpoint deleted: {checkpoint_file}")
                return True
            else:
                logger.warning(f"Checkpoint not found: {checkpoint_file}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
            return False
    
    def create_state_snapshot(
        self,
        visited: set,
        queue: list,
        results: list,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a state snapshot for checkpointing.
        
        Args:
            visited: Set of visited URLs
            queue: Current queue of URLs to crawl
            results: Crawl results so far
            config: Crawler configuration
            
        Returns:
            State dictionary
        """
        return {
            'visited': list(visited),
            'queue': queue,
            'results': [r.to_dict() if hasattr(r, 'to_dict') else r for r in results],
            'config': config,
            'stats': {
                'visited_count': len(visited),
                'queue_size': len(queue),
                'results_count': len(results)
            }
        }
    
    def cleanup_old_checkpoints(self, keep_count: int = 10) -> None:
        """
        Remove old checkpoints, keeping only the most recent ones.
        
        Args:
            keep_count: Number of checkpoints to keep
        """
        try:
            checkpoints = self.list_checkpoints()
            
            if len(checkpoints) > keep_count:
                to_delete = checkpoints[keep_count:]
                
                for checkpoint in to_delete:
                    self.delete(checkpoint['name'])
                
                logger.info(f"Cleaned up {len(to_delete)} old checkpoints")
                
        except Exception as e:
            logger.error(f"Failed to cleanup checkpoints: {e}")
