"""
Universal Experience Extraction Module for GRPO Training
通用经验提炼模块（用于GRPO训练）

Provides unified experience extraction logic for both Generators and Critic.
为Generator和Critic提供统一的经验提炼逻辑。
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from engine.scaffolder import LLMClient


class ExperienceExtractor:
    """
    Universal experience extractor for GRPO training.
    通用经验提炼器（用于GRPO训练）
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None, tau: float = 0.05, verbose: bool = True):
        """
        Initialize experience extractor.
        
        Args:
            llm_client: LLM client for experience extraction
            tau: GRPO threshold (σ > τ triggers extraction)
            verbose: Print progress messages
        """
        self.llm_client = llm_client or LLMClient()
        self.tau = tau
        self.verbose = verbose
        
        # Get absolute path to project root
        project_root = Path(__file__).parent.parent
        
        # Load prompts using absolute paths
        self.generator_prompt = self._load_prompt(str(project_root / "prompts" / "generator_experience_extraction.txt"))
        self.critic_prompt = self._load_prompt(str(project_root / "prompts" / "critic_experience_extraction.txt"))
        
        if self.verbose:
            print(f"✓ ExperienceExtractor initialized (τ={tau})")
    
    def _print(self, message: str, **kwargs):
        """Print if verbose mode is enabled."""
        if self.verbose:
            print(message, **kwargs)
    
    def _load_prompt(self, path: str) -> str:
        """Load prompt template from file."""
        prompt_path = Path(path)
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise FileNotFoundError(f"Prompt file not found: {path}")
    
    def extract_generator_experience(
        self,
        generator_id: str,
        problem: Dict[str, Any],
        rollouts: List[Dict[str, Any]],
        ground_truth: str
    ) -> Optional[str]:
        """
        Extract experience for a Generator based on its rollouts.
        为Generator提取经验（基于其rollouts）
        
        Args:
            generator_id: "generator_1", "generator_2", or "generator_3"
            problem: Problem data with 'id' and 'text'
            rollouts: List of 3 rollouts with rewards (each rollout must have:
                      'answer', 'r_ans', 'r_logic', 'r_graph', 'r_total')
            ground_truth: Standard answer
        
        Returns:
            Extracted experience string or None
        """
        # Step 1: Calculate GRPO statistics
        rewards = [r['r_total'] for r in rollouts]
        μ = float(np.mean(rewards))
        σ = float(np.std(rewards))
        
        self._print(f"  {generator_id}: μ={μ:.3f}, σ={σ:.3f} ", end="")
        
        # Step 2: Check GRPO threshold
        if σ <= self.tau:
            self._print(f"→ Skip (σ≤τ)")
            return None
        
        self._print(f"→ Extract (σ>τ)")
        
        # Step 3: Load current experiences
        current_experiences = self._load_experiences(generator_id)
        current_exp_str = "\n".join([
            f"{exp['id']}: {exp['content']}" for exp in current_experiences
        ]) if current_experiences else "No experiences yet"
        
        # Step 4: Prepare prompt
        import json
        
        # Format scaffolds as readable JSON
        def format_scaffold(scaffold):
            if scaffold is None:
                return "None (generation failed)"
            try:
                return json.dumps(scaffold, indent=2, ensure_ascii=False)
            except:
                return str(scaffold)
        
        prompt = self.generator_prompt.format(
            generator_id=generator_id,
            num_rollouts=len(rollouts),
            problem_text=problem['text'],
            ground_truth=ground_truth,
            # Rollout 1
            rollout_1_scaffold=format_scaffold(rollouts[0].get('scaffold')),
            rollout_1_answer=rollouts[0]['answer'],
            rollout_1_r_ans=rollouts[0]['r_ans'],
            rollout_1_r_logic=rollouts[0]['r_logic'],
            rollout_1_r_graph=rollouts[0]['r_graph'],
            rollout_1_r_total=rollouts[0]['r_total'],
            # Rollout 2
            rollout_2_scaffold=format_scaffold(rollouts[1].get('scaffold')),
            rollout_2_answer=rollouts[1]['answer'],
            rollout_2_r_ans=rollouts[1]['r_ans'],
            rollout_2_r_logic=rollouts[1]['r_logic'],
            rollout_2_r_graph=rollouts[1]['r_graph'],
            rollout_2_r_total=rollouts[1]['r_total'],
            # Rollout 3
            rollout_3_scaffold=format_scaffold(rollouts[2].get('scaffold')),
            rollout_3_answer=rollouts[2]['answer'],
            rollout_3_r_ans=rollouts[2]['r_ans'],
            rollout_3_r_logic=rollouts[2]['r_logic'],
            rollout_3_r_graph=rollouts[2]['r_graph'],
            rollout_3_r_total=rollouts[2]['r_total'],
            # Current experiences
            current_experiences=current_exp_str
        )
        
        # Step 5: Call LLM for experience extraction
        try:
            response = self.llm_client.complete(prompt, temperature=0.3)
            operations = self._parse_json_response(response)
            
            if operations and len(operations) > 0:
                # Apply operations to experience library
                for op in operations:
                    action = op.get('action')
                    
                    if action == 'add':
                        self._add_experience(
                            generator_id,
                            op['content'],
                            op.get('category', 'causal_graph'),
                            problem['id']
                        )
                        self._print(f"    ✅ Added: {op['content'][:50]}...")
                    
                    elif action == 'modify':
                        self._modify_experience(
                            generator_id,
                            op['id'],
                            op['content'],
                            problem['id']
                        )
                        self._print(f"    🔄 Modified {op['id']}: {op['content'][:50]}...")
                    
                    elif action == 'delete':
                        self._delete_experience(
                            generator_id,
                            op['id']
                        )
                        self._print(f"    🗑️  Deleted {op['id']}: {op.get('reason', 'No reason')[:50]}...")
                
                return f"Applied {len(operations)} operations to experience library"
            else:
                self._print(f"    ℹ️  No operations to apply")
                return None
                
        except Exception as e:
            self._print(f"    ⚠️  Extraction failed: {e}")
            return None
    
    def extract_critic_experience(
        self,
        problem: Dict[str, Any],
        fusion_results: List[Dict[str, Any]],
        ground_truth: str
    ) -> Optional[str]:
        """
        Extract experience for Critic based on fusion results.
        为Critic提取经验（基于融合结果）
        
        Args:
            problem: Problem data with 'id' and 'text'
            fusion_results: List of 3 fusion results (one per Generator)
                           Each must have: 'answer', 'is_correct', 'r_ans', 
                           'r_logic', 'r_graph', 'r_fusion', 'r_total'
            ground_truth: Standard answer
        
        Returns:
            Extracted experience string or None
        """
        # Step 1: Calculate GRPO statistics
        rewards = [fr['r_total'] for fr in fusion_results]
        μ = float(np.mean(rewards))
        σ = float(np.std(rewards))
        
        self._print(f"  Critic: μ={μ:.3f}, σ={σ:.3f} ", end="")
        
        # Step 2: Check GRPO threshold
        if σ <= self.tau:
            self._print(f"→ Skip (σ≤τ)")
            return None
        
        self._print(f"→ Extract (σ>τ)")
        
        # Step 3: Load current Critic experiences
        current_experiences = self._load_experiences("critic")
        current_exp_str = "\n".join([
            f"{exp['id']}: {exp['content']}" for exp in current_experiences
        ]) if current_experiences else "No experiences yet"
        
        # Step 4: Prepare prompt
        import json
        
        # Format DAGs as readable JSON
        def format_dag(dag):
            if dag is None:
                return "None (fusion failed)"
            try:
                return json.dumps(dag, indent=2, ensure_ascii=False)
            except:
                return str(dag)
        
        prompt = self.critic_prompt.format(
            problem_text=problem['text'],
            ground_truth=ground_truth,
            # Fusion 1
            fusion_1_dag=format_dag(fusion_results[0].get('fused_dag')),
            fusion_1_answer=fusion_results[0]['answer'],
            fusion_1_result="Correct" if fusion_results[0]['is_correct'] else "Incorrect",
            fusion_1_r_ans=fusion_results[0]['r_ans'],
            fusion_1_r_logic=fusion_results[0]['r_logic'],
            fusion_1_r_graph=fusion_results[0]['r_graph'],
            fusion_1_r_fusion=fusion_results[0]['r_fusion'],
            fusion_1_r_total=fusion_results[0]['r_total'],
            # Fusion 2
            fusion_2_dag=format_dag(fusion_results[1].get('fused_dag')),
            fusion_2_answer=fusion_results[1]['answer'],
            fusion_2_result="Correct" if fusion_results[1]['is_correct'] else "Incorrect",
            fusion_2_r_ans=fusion_results[1]['r_ans'],
            fusion_2_r_logic=fusion_results[1]['r_logic'],
            fusion_2_r_graph=fusion_results[1]['r_graph'],
            fusion_2_r_fusion=fusion_results[1]['r_fusion'],
            fusion_2_r_total=fusion_results[1]['r_total'],
            # Fusion 3
            fusion_3_dag=format_dag(fusion_results[2].get('fused_dag')),
            fusion_3_answer=fusion_results[2]['answer'],
            fusion_3_result="Correct" if fusion_results[2]['is_correct'] else "Incorrect",
            fusion_3_r_ans=fusion_results[2]['r_ans'],
            fusion_3_r_logic=fusion_results[2]['r_logic'],
            fusion_3_r_graph=fusion_results[2]['r_graph'],
            fusion_3_r_fusion=fusion_results[2]['r_fusion'],
            fusion_3_r_total=fusion_results[2]['r_total'],
            # Current experiences
            current_experiences=current_exp_str
        )
        
        # Step 5: Call LLM for experience extraction
        try:
            response = self.llm_client.complete(prompt, temperature=0.3)
            operations = self._parse_json_response(response)
            
            if operations and len(operations) > 0:
                # Apply operations to Critic experience library
                for op in operations:
                    action = op.get('action')
                    
                    if action == 'add':
                        self._add_experience(
                            "critic",
                            op['content'],
                            op.get('category', 'fusion_strategy'),
                            problem['id']
                        )
                        self._print(f"    ✅ Added: {op['content'][:50]}...")
                    
                    elif action == 'modify':
                        self._modify_experience(
                            "critic",
                            op['id'],
                            op['content'],
                            problem['id']
                        )
                        self._print(f"    🔄 Modified {op['id']}: {op['content'][:50]}...")
                    
                    elif action == 'delete':
                        self._delete_experience(
                            "critic",
                            op['id']
                        )
                        self._print(f"    🗑️  Deleted {op['id']}: {op.get('reason', 'No reason')[:50]}...")
                
                return f"Applied {len(operations)} operations to experience library"
            else:
                self._print(f"    ℹ️  No operations to apply")
                return None
                
        except Exception as e:
            self._print(f"    ⚠️  Extraction failed: {e}")
            return None
    
    def _parse_json_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse JSON from LLM response."""
        try:
            # Find JSON block
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                return data.get('operations', [])
        except Exception as e:
            self._print(f"    ⚠️  JSON parsing error: {e}")
        
        return []
    
    def _load_experiences(self, agent_id: str) -> List[Dict[str, Any]]:
        """Load existing experiences for an agent."""
        # Get absolute path to project root
        project_root = Path(__file__).parent.parent
        exp_file = project_root / "data" / "grpo_experiences" / f"{agent_id}_experiences.json"
        
        if exp_file.exists():
            try:
                with open(exp_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self._print(f"    ⚠️  Error loading experiences: {e}")
                return []
        return []
    
    def _add_experience(
        self,
        agent_id: str,
        content: str,
        category: str,
        source_problem: str
    ):
        """Add a new experience to the library."""
        experiences = self._load_experiences(agent_id)
        
        # Generate ID
        if agent_id == "critic":
            prefix = "C"
        else:
            prefix = f"G{agent_id.split('_')[-1]}"
        
        exp_id = f"{prefix}-{len(experiences)+1:03d}"
        
        # Add new experience
        experiences.append({
            "id": exp_id,
            "content": content,
            "category": category,
            "source_problem": source_problem,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        
        self._save_experiences(agent_id, experiences)
    
    def _modify_experience(
        self,
        agent_id: str,
        exp_id: str,
        new_content: str,
        source_problem: str
    ):
        """Modify an existing experience."""
        experiences = self._load_experiences(agent_id)
        
        for exp in experiences:
            if exp['id'] == exp_id:
                exp['content'] = new_content
                exp['updated_at'] = datetime.now().isoformat()
                exp['last_modified_by'] = source_problem
                break
        
        self._save_experiences(agent_id, experiences)
    
    def _delete_experience(
        self,
        agent_id: str,
        exp_id: str
    ):
        """Delete an experience from the library."""
        experiences = self._load_experiences(agent_id)
        experiences = [exp for exp in experiences if exp['id'] != exp_id]
        self._save_experiences(agent_id, experiences)
    
    def _save_experiences(
        self,
        agent_id: str,
        experiences: List[Dict[str, Any]]
    ):
        """Save experiences to file."""
        project_root = Path(__file__).parent.parent
        exp_file = project_root / "data" / "grpo_experiences" / f"{agent_id}_experiences.json"
        exp_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(exp_file, 'w', encoding='utf-8') as f:
            json.dump(experiences, f, indent=2, ensure_ascii=False)


# Example usage
if __name__ == "__main__":
    print("Experience Extractor Module")
    print("通用经验提炼模块")
    print("\nFeatures:")
    print("- GRPO-based experience extraction (σ > τ)")
    print("- Unified logic for both Generators and Critic")
    print("- Automatic experience storage and ID generation")

