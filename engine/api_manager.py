"""
API Key Manager for Multi-Agent Training
多智能体训练的API密钥管理器

Manages API keys for different agents (generators and critic).
管理不同智能体（生成器和批判者）的API密钥。
"""

import json
from pathlib import Path
from typing import Dict, Optional


class APIKeyManager:
    """
    API Key Manager for multi-agent system.
    多智能体系统的API密钥管理器
    """
    
    def __init__(self, config_path: str = "data/api_keys/api_config.json"):
        """
        Initialize API Key Manager.
        
        Args:
            config_path: Path to API configuration JSON file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load API configuration from file."""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(
                f"API config not found: {self.config_path}\n"
                f"Please create the config file first. See data/api_keys/api_config.json.example"
            )
    
    def get_api_key(self, role: str) -> str:
        """
        Get API key for a specific role.
        
        Args:
            role: Role identifier ('generator_1', 'generator_2', 'generator_3', 
                  'critic', 'reward_evaluator', etc.)
        
        Returns:
            API key string
        
        Raises:
            ValueError: If role not found in config
        """
        if role in self.config:
            return self.config[role]['api_key']
        else:
            raise ValueError(
                f"No API key found for role: {role}\n"
                f"Available roles: {list(self.config.keys())}"
            )
    
    def get_role_config(self, role: str) -> Dict:
        """
        Get complete configuration for a role.
        
        Args:
            role: Role identifier
        
        Returns:
            Configuration dictionary with 'api_key', 'description', 'role'
        """
        if role in self.config:
            return self.config[role]
        else:
            raise ValueError(f"No config found for role: {role}")
    
    def get_description(self, role: str) -> str:
        """Get human-readable description for a role."""
        config = self.get_role_config(role)
        return config.get('description', role)
    
    def list_roles(self) -> list:
        """List all available roles."""
        return list(self.config.keys())
    
    def validate_config(self) -> bool:
        """
        Validate that all required roles have API keys configured.
        
        Returns:
            True if valid, False otherwise
        """
        required_roles = ['generator_1', 'generator_2', 'generator_3', 'critic']
        
        for role in required_roles:
            if role not in self.config:
                print(f"❌ Missing required role: {role}")
                return False
            
            if 'api_key' not in self.config[role] or not self.config[role]['api_key']:
                print(f"❌ Empty API key for role: {role}")
                return False
        
        print(f"✓ API configuration validated: {len(required_roles)} required roles OK")
        return True


# Example usage
if __name__ == "__main__":
    print("API Key Manager")
    print("="*60)
    
    try:
        manager = APIKeyManager()
        
        if manager.validate_config():
            print("\n✓ Configuration is valid")
            print(f"\nAvailable roles:")
            for role in manager.list_roles():
                desc = manager.get_description(role)
                key_preview = manager.get_api_key(role)[:15] + "..."
                print(f"  - {role}: {desc} ({key_preview})")
        else:
            print("\n❌ Configuration validation failed")
            
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease create data/api_keys/api_config.json with your API keys.")
