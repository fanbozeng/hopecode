"""
Training-Free GRPO Experience Manager for Multi-Agent Scaffolder
基于Training-Free GRPO的多智能体经验管理器

This module manages experiential knowledge for:
- 3 Generator Agents (causal graph generation)
- 1 Critic Agent (fusion and refinement)

本模块管理以下智能体的经验知识：
- 3个生成器智能体（因果图生成）
- 1个批判者智能体（融合和精炼）
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Experience:
    """
    Single experience entry.
    单条经验记录
    
    Attributes:
        id: Unique identifier (e.g., "G1-001", "C-005")
              唯一标识符
        content: The experience text
                 经验内容
        category: Experience category (e.g., "causal_graph", "validation", "fusion")
                  经验类别
        success_count: Number of times this experience led to success
                      该经验带来成功的次数
        usage_count: Total times this experience was used
                     该经验被使用的总次数
        created_at: Creation timestamp
                    创建时间
        source_problem: Problem that generated this experience
                       产生该经验的问题
    """
    id: str
    content: str
    category: str = "general"
    success_count: int = 0
    usage_count: int = 0
    created_at: str = ""
    source_problem: str = ""


class GRPOExperienceManager:
    """
    Experience Manager for Training-Free GRPO.
    训练自由GRPO的经验管理器
    
    Manages separate experience libraries for:
    - Shared experiences (all agents)
    - Generator 1, 2, 3 experiences
    - Critic experiences
    
    管理以下经验库：
    - 共享经验（所有智能体）
    - 生成器1、2、3的经验
    - 批判者的经验
    """
    
    def __init__(
        self,
        experience_dir: str = "data/grpo_experiences",
        verbose: bool = True
    ):
        """
        Initialize GRPO Experience Manager.
        初始化GRPO经验管理器
        
        Args:
            experience_dir: Directory to store experience files
                           存储经验文件的目录
            verbose: Whether to print detailed information
                    是否打印详细信息
        """
        self.experience_dir = Path(experience_dir)
        self.experience_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        
        # Experience libraries for each agent
        # 每个智能体的经验库
        self.experiences = {
            'shared': [],       # 共享经验
            'generator_1': [],  # 生成器1的经验
            'generator_2': [],  # 生成器2的经验
            'generator_3': [],  # 生成器3的经验
            'critic': []        # 批判者的经验
        }
        
        # Load existing experiences
        # 加载现有经验
        self._load_all_experiences()
        
        # Training statistics
        # 训练统计
        self.training_stats = {
            'total_problems': 0,
            'total_experiences_added': 0,
            'total_experiences_modified': 0,
            'total_experiences_deleted': 0,
            'epochs_completed': 0
        }
    
    def _print(self, message: str):
        """Print if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def _load_all_experiences(self):
        """Load all experience libraries from disk."""
        for agent_type in self.experiences.keys():
            file_path = self.experience_dir / f"{agent_type}_experiences.json"
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Convert to Experience objects
                    self.experiences[agent_type] = [
                        Experience(**exp) for exp in data
                    ]
                    
                    self._print(f"✓ Loaded {len(data)} experiences for {agent_type}")
                    self._print(f"✓ 为 {agent_type} 加载了 {len(data)} 条经验")
                    
                except Exception as e:
                    self._print(f"⚠ Failed to load {agent_type}: {e}")
                    self.experiences[agent_type] = []
            else:
                self._print(f"ℹ No existing experiences for {agent_type}")
    
    def _save_experiences(self, agent_type: str):
        """
        Save experiences for a specific agent type.
        保存特定智能体类型的经验
        
        Args:
            agent_type: Type of agent ('shared', 'generator_1', etc.)
                       智能体类型
        """
        file_path = self.experience_dir / f"{agent_type}_experiences.json"
        
        # Convert Experience objects to dict
        data = [asdict(exp) for exp in self.experiences[agent_type]]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self._print(f"✓ Saved {len(data)} experiences for {agent_type}")
    
    def get_experiences_for_agent(
        self, 
        agent_type: str, 
        include_shared: bool = True,
        format_as_prompt: bool = True
    ) -> str:
        """
        Get experiences for a specific agent.
        获取特定智能体的经验
        
        Args:
            agent_type: 'generator_1', 'generator_2', 'generator_3', or 'critic'
            include_shared: Whether to include shared experiences
                           是否包含共享经验
            format_as_prompt: Whether to format as prompt text
                             是否格式化为提示文本
        
        Returns:
            Formatted experience text or list of Experience objects
            格式化的经验文本或Experience对象列表
        """
        # Collect experiences
        experiences = []
        
        # Add shared experiences first
        if include_shared:
            experiences.extend(self.experiences['shared'])
        
        # Add agent-specific experiences
        if agent_type in self.experiences:
            experiences.extend(self.experiences[agent_type])
        
        if not format_as_prompt:
            return experiences
        
        # Format as prompt text
        if not experiences:
            return ""
        
        formatted = []
        formatted.append("**LEARNED EXPERIENCES / 学到的经验:**\n")
        formatted.append("You MUST carefully consider and apply the following experiences:\n")
        formatted.append("你必须仔细考虑并应用以下经验：\n")
        
        for exp in experiences:
            category_tag = f"[{exp.category}]" if exp.category != "general" else ""
            formatted.append(f"\n{exp.id}. {category_tag} {exp.content}")
            
            # Add success rate if available
            if exp.usage_count > 0:
                success_rate = exp.success_count / exp.usage_count
                formatted.append(f"   (Success rate: {success_rate:.1%} | 成功率: {success_rate:.1%})")
        
        formatted.append("\n---\n")
        
        return "\n".join(formatted)
    
    def add_experience(
        self,
        agent_type: str,
        content: str,
        category: str = "general",
        source_problem: str = "",
        save: bool = True
    ) -> str:
        """
        Add a new experience.
        添加新经验
        
        Args:
            agent_type: Target agent type
            content: Experience content
            category: Experience category
            source_problem: Problem that generated this experience
            save: Whether to save immediately
        
        Returns:
            Experience ID
        """
        # Generate unique ID
        prefix = agent_type[0].upper() if agent_type != 'shared' else 'S'
        if agent_type.startswith('generator'):
            prefix = f"G{agent_type[-1]}"
        elif agent_type == 'critic':
            prefix = "C"
        
        existing_ids = [
            exp.id for exp in self.experiences[agent_type]
            if exp.id.startswith(prefix)
        ]
        
        if existing_ids:
            # Extract numbers and find max
            numbers = [int(eid.split('-')[1]) for eid in existing_ids]
            next_num = max(numbers) + 1
        else:
            next_num = 1
        
        exp_id = f"{prefix}-{next_num:03d}"
        
        # Create experience
        experience = Experience(
            id=exp_id,
            content=content,
            category=category,
            created_at=datetime.now().isoformat(),
            source_problem=source_problem[:100] if source_problem else ""
        )
        
        self.experiences[agent_type].append(experience)
        
        # Update statistics
        self.training_stats['total_experiences_added'] += 1
        
        if save:
            self._save_experiences(agent_type)
        
        self._print(f"✅ Added experience {exp_id} to {agent_type}")
        self._print(f"   {content[:60]}...")
        
        return exp_id
    
    def modify_experience(
        self,
        exp_id: str,
        new_content: str,
        save: bool = True
    ) -> bool:
        """
        Modify an existing experience.
        修改现有经验
        
        Args:
            exp_id: Experience ID
            new_content: New content
            save: Whether to save immediately
        
        Returns:
            True if successful, False otherwise
        """
        # Find the experience
        for agent_type, exp_list in self.experiences.items():
            for exp in exp_list:
                if exp.id == exp_id:
                    old_content = exp.content
                    exp.content = new_content
                    
                    # Update statistics
                    self.training_stats['total_experiences_modified'] += 1
                    
                    if save:
                        self._save_experiences(agent_type)
                    
                    self._print(f"✏️ Modified experience {exp_id}")
                    self._print(f"   Old: {old_content[:50]}...")
                    self._print(f"   New: {new_content[:50]}...")
                    
                    return True
        
        self._print(f"⚠ Experience {exp_id} not found")
        return False
    
    def delete_experience(
        self,
        exp_id: str,
        save: bool = True
    ) -> bool:
        """
        Delete an experience.
        删除经验
        
        Args:
            exp_id: Experience ID
            save: Whether to save immediately
        
        Returns:
            True if successful, False otherwise
        """
        for agent_type, exp_list in self.experiences.items():
            for i, exp in enumerate(exp_list):
                if exp.id == exp_id:
                    deleted = exp_list.pop(i)
                    
                    # Update statistics
                    self.training_stats['total_experiences_deleted'] += 1
                    
                    if save:
                        self._save_experiences(agent_type)
                    
                    self._print(f"🗑️ Deleted experience {exp_id}")
                    self._print(f"   {deleted.content[:50]}...")
                    
                    return True
        
        self._print(f"⚠ Experience {exp_id} not found")
        return False
    
    def record_experience_usage(
        self,
        exp_id: str,
        success: bool,
        save: bool = False
    ):
        """
        Record that an experience was used.
        记录经验的使用情况
        
        Args:
            exp_id: Experience ID
            success: Whether it led to success
            save: Whether to save immediately
        """
        for agent_type, exp_list in self.experiences.items():
            for exp in exp_list:
                if exp.id == exp_id:
                    exp.usage_count += 1
                    if success:
                        exp.success_count += 1
                    
                    if save:
                        self._save_experiences(agent_type)
                    return
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get experience statistics.
        获取经验统计信息
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'training_stats': self.training_stats.copy(),
            'experience_counts': {
                agent_type: len(exp_list)
                for agent_type, exp_list in self.experiences.items()
            },
            'total_experiences': sum(
                len(exp_list) for exp_list in self.experiences.values()
            )
        }
        
        # Add success rates
        for agent_type, exp_list in self.experiences.items():
            if exp_list:
                total_usage = sum(exp.usage_count for exp in exp_list)
                total_success = sum(exp.success_count for exp in exp_list)
                
                if total_usage > 0:
                    stats[f'{agent_type}_success_rate'] = total_success / total_usage
        
        return stats
    
    def print_summary(self):
        """Print a summary of all experiences."""
        print("\n" + "="*80)
        print(" GRPO Experience Summary")
        print(" GRPO经验总结")
        print("="*80 + "\n")
        
        stats = self.get_statistics()
        
        print(f"📊 Total Experiences: {stats['total_experiences']}")
        print(f"📊 总经验数: {stats['total_experiences']}\n")
        
        for agent_type, count in stats['experience_counts'].items():
            print(f"  - {agent_type}: {count} experiences")
            
            # Show success rate if available
            rate_key = f'{agent_type}_success_rate'
            if rate_key in stats:
                print(f"    Success rate: {stats[rate_key]:.1%}")
        
        print(f"\n📈 Training Statistics:")
        print(f"  - Problems processed: {stats['training_stats']['total_problems']}")
        print(f"  - Experiences added: {stats['training_stats']['total_experiences_added']}")
        print(f"  - Experiences modified: {stats['training_stats']['total_experiences_modified']}")
        print(f"  - Experiences deleted: {stats['training_stats']['total_experiences_deleted']}")
        print(f"  - Epochs completed: {stats['training_stats']['epochs_completed']}")
        
        print("\n" + "="*80)
    
    def save_all(self):
        """Save all experience libraries."""
        for agent_type in self.experiences.keys():
            self._save_experiences(agent_type)
        
        self._print("✅ Saved all experience libraries")
    
    def export_for_deployment(self, output_path: str):
        """
        Export experiences for deployment.
        导出经验用于部署
        
        Args:
            output_path: Output file path
        """
        export_data = {
            'experiences': {
                agent_type: [asdict(exp) for exp in exp_list]
                for agent_type, exp_list in self.experiences.items()
            },
            'statistics': self.get_statistics(),
            'export_time': datetime.now().isoformat()
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self._print(f"📦 Exported experiences to: {output_file}")


# Example usage
if __name__ == "__main__":
    # Initialize manager
    manager = GRPOExperienceManager()
    
    # Add some test experiences
    manager.add_experience(
        agent_type='generator_1',
        content="When constructing causal graphs, always validate that all variables in causal_links exist in the knowns dictionary",
        category="causal_graph_validation"
    )
    
    manager.add_experience(
        agent_type='critic',
        content="When merging proposals, prioritize the one with more complete causal links and consistent variable definitions",
        category="fusion_strategy"
    )
    
    manager.add_experience(
        agent_type='shared',
        content="Always verify that the target_variable is correctly identified before constructing the computation plan",
        category="general_validation"
    )
    
    # Get experiences for generator 1
    print("\n" + "="*80)
    print("Experiences for Generator 1:")
    print("="*80)
    print(manager.get_experiences_for_agent('generator_1'))
    
    # Print summary
    manager.print_summary()




