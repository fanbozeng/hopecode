"""
API密钥管理器
管理不同智能体（Generator和Critic）的API密钥
"""

import json
from pathlib import Path
from typing import Dict


class APIKeyManager:
    """API密钥管理器"""

    def __init__(self, config_path: str = "data/api_keys/api_config.json"):
        """
        初始化API密钥管理器

        Args:
            config_path: API配置JSON文件路径
        """
        # 处理相对路径，相对于项目根目录
        if not Path(config_path).is_absolute():
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent  # 从engine/目录上到项目根目录
            self.config_path = project_root / config_path
        else:
            self.config_path = Path(config_path)

        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """从文件加载API配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(
                f"找不到API配置文件: {self.config_path}\n"
                f"请先创建配置文件，参考 data/api_keys/api_config.json.example"
            )
    
    def get_api_key(self, role: str) -> str:
        """
        获取指定角色的API密钥

        Args:
            role: 角色标识 ('generator_1', 'generator_2', 'generator_3', 'critic'等)

        Returns:
            API密钥字符串

        Raises:
            ValueError: 找不到角色时抛出异常
        """
        if role in self.config:
            return self.config[role]['api_key']
        else:
            raise ValueError(
                f"找不到角色 {role} 的API密钥\n"
                f"可用角色: {list(self.config.keys())}"
            )

    def get_role_config(self, role: str) -> Dict:
        """
        获取角色的完整配置

        Args:
            role: 角色标识

        Returns:
            角色配置字典 (包含api_key, description, role等)
        """
        if role in self.config:
            return self.config[role]
        else:
            raise ValueError(f"找不到角色 {role} 的配置")

    def get_description(self, role: str) -> str:
        """获取角色描述"""
        config = self.get_role_config(role)
        return config.get('description', role)

    def list_roles(self) -> list:
        """列出所有可用角色"""
        return list(self.config.keys())

    def validate_config(self) -> bool:
        """
        验证配置是否完整

        Returns:
            True: 配置有效, False: 配置无效
        """
        required_roles = ['generator_1', 'generator_2', 'generator_3', 'critic']

        for role in required_roles:
            if role not in self.config:
                return False

            if 'api_key' not in self.config[role] or not self.config[role]['api_key']:
                return False

        return True


# 使用示例
if __name__ == "__main__":
    try:
        manager = APIKeyManager()

        if manager.validate_config():
            print("✓ API配置验证通过")
            print("可用角色:")
            for role in manager.list_roles():
                desc = manager.get_description(role)
                key_preview = manager.get_api_key(role)[:15] + "..."
                print(f"  - {role}: {desc}")
        else:
            print("❌ API配置验证失败")

    except FileNotFoundError as e:
        print(f"❌ 错误: {e}")
        print("\n请在 data/api_keys/api_config.json 中配置API密钥。")
