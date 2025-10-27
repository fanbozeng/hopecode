"""
Training-Free GRPO Trainer (用户架构版本)
训练自由GRPO训练器

Implements per-generator experience learning:
实现每个生成器独立的经验学习：

Question → Generator 1 → [R1.1, R1.2, R1.3] → Critic fusion → Scaffold 1 → Answer 1 → Reward 1
Question → Generator 2 → [R2.1, R2.2, R2.3] → Critic fusion → Scaffold 2 → Answer 2 → Reward 2  
Question → Generator 3 → [R3.1, R3.2, R3.3] → Critic fusion → Scaffold 3 → Answer 3 → Reward 3

Then update each generator's and critic's experience based on their performance.
然后根据各自的表现更新每个生成器和批判者的经验。
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime

# Import LLM client and computer
from engine.scaffolder import LLMClient
from engine.llm_computer import LLMComputer


class TrainingFreeGRPOTrainer:
    """
    Training-Free GRPO Trainer - Per-Generator Architecture.
    训练自由GRPO训练器 - 每生成器架构
    
    Key features:
    - Each generator produces multiple rollouts (default: 3)
    - Critic fuses each generator's rollouts separately (not mixing all rollouts)
    - Get 3 final answers (one per generator)
    - Update each LLM's experience individually based on its own performance
    
    主要特点：
    - 每个生成器产生多个rollouts（默认：3）
    - Critic分别融合每个生成器的rollouts（不混合所有rollouts）
    - 得到3个最终答案（每个生成器一个）
    - 根据各自的表现单独更新每个LLM的经验
    """
    
    def __init__(
        self,
        causal_engine,  # CausalReasoningEngine instance with MultiAgentScaffolder
        experience_manager,  # GRPOExperienceManager instance
        llm_client: Optional[LLMClient] = None,
        rollouts_per_generator: int = 3,  # Each generator produces 3 rollouts
        num_epochs: int = 3,
        verbose: bool = True
    ):
        """
        Initialize Training-Free GRPO Trainer.
        初始化训练自由GRPO训练器
        
        Args:
            causal_engine: CausalReasoningEngine with MultiAgentScaffolder
            experience_manager: GRPOExperienceManager
            llm_client: LLM for semantic advantage extraction
            rollouts_per_generator: Rollouts per generator (default: 3)
            num_epochs: Training epochs (default: 3)
            verbose: Print detailed info
        """
        self.engine = causal_engine
        self.experience_manager = experience_manager
        self.llm_client = llm_client or LLMClient()
        self.llm_computer = LLMComputer(verbose=False)  # For executing scaffolds
        self.rollouts_per_generator = rollouts_per_generator
        self.num_epochs = num_epochs
        self.verbose = verbose
        
        # Load answer comparison prompt for accurate evaluation
        # 加载答案比较提示词以实现准确评估
        self.answer_comparison_prompt = self._load_answer_comparison_prompt()
        
        # Configure scaffolder for GRPO training
        # 配置scaffolder用于GRPO训练
        if hasattr(self.engine, 'scaffolder'):
            # Ensure experience_manager is injected (failsafe mechanism)
            # 确保经验管理器已注入（保险机制）
            if not hasattr(self.engine.scaffolder, 'experience_manager') or \
               self.engine.scaffolder.experience_manager is None:
                self.engine.scaffolder.experience_manager = self.experience_manager
                self._print("✓ Experience manager auto-injected to scaffolder")
                self._print("✓ 经验管理器已自动注入到scaffolder")
            
            self.engine.scaffolder.rollouts_per_generator = rollouts_per_generator
            self._print(f"✓ Configured scaffolder: {rollouts_per_generator} rollouts per generator")
        
        # Training log
        self.training_log = []
        
        # Load prompts
        self._load_prompts()
        
        self._print("🚀 Training-Free GRPO Trainer initialized")
        self._print(f"   - Rollouts per generator: {rollouts_per_generator}")
        self._print(f"   - Epochs: {num_epochs}")
        self._print("🚀 训练自由GRPO训练器已初始化")
        self._print(f"   - 每个生成器的rollout数: {rollouts_per_generator}")
        self._print(f"   - Epoch数: {num_epochs}")
    
    def _print(self, message: str):
        """Print if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def _load_prompts(self):
        """Load prompts for experience extraction."""
        # Simplified prompts for generator-specific experience extraction
        self.generator_advantage_prompt = """
You are analyzing the rollouts from Generator {generator_id} for a single problem.

**Problem:**
{problem}

**Ground Truth:**
{ground_truth}

**Generator {generator_id}'s Performance:**
- Generated {num_rollouts} rollouts
- After critic fusion: Final answer = {final_answer}
- Result: {result} (Correct/Incorrect)

**Current Experiences for Generator {generator_id}:**
{current_experiences}

Based on this generator's performance, what experience should be added/modified/deleted?

Focus on:
1. What mistakes did this generator make in its causal graph construction?
2. What patterns should this generator learn for similar problems?
3. Are existing experiences being applied correctly?

Provide recommendations in JSON format:
```json
{{
    "operations": [
        {{
            "action": "add",
            "content": "New experience (≤32 words)",
            "category": "causal_graph|validation|problem_solving",
            "reason": "Why this helps Generator {generator_id}"
        }},
        {{
            "action": "modify",
            "experience_id": "G{generator_id}-001",
            "new_content": "Modified experience",
            "reason": "Improvement reason"
        }},
        {{
            "action": "delete",
            "experience_id": "G{generator_id}-003",
            "reason": "Why remove"
        }}
    ],
    "summary": "Overall analysis for Generator {generator_id}"
}}
```
"""

        self.critic_advantage_prompt = """
You are analyzing the Critic's fusion performance across multiple generators.

**Problem:**
{problem}

**Ground Truth:**
{ground_truth}

**Critic's Performance:**
{critic_performance}

**Current Critic Experiences:**
{current_experiences}

Analyze:
1. Did the critic successfully fuse rollouts from each generator?
2. What fusion strategies worked well?
3. How can the critic better identify high-quality proposals?

Provide recommendations in JSON format:
```json
{{
    "operations": [
        {{
            "action": "add",
            "content": "New fusion experience (≤32 words)",
            "category": "fusion_strategy|validation|conflict_resolution",
            "reason": "Why this helps fusion"
        }}
    ],
    "summary": "Critic fusion improvement insights"
}}
```
"""
    
    def train(
        self,
        training_problems: List[Dict[str, Any]],
        save_checkpoint: bool = True
    ):
        """
        Train using Training-Free GRPO.
        使用训练自由GRPO训练
        
        Args:
            training_problems: Problems with ground truth
            save_checkpoint: Save after each epoch
        """
        self._print("\n" + "="*80)
        self._print("🎓 Training-Free GRPO Training (Per-Generator Architecture)")
        self._print("🎓 训练自由GRPO训练（每生成器架构）")
        self._print("="*80)
        self._print(f"\n📊 Training Set: {len(training_problems)} problems")
        self._print(f"🔄 Epochs: {self.num_epochs}")
        self._print(f"👥 Rollouts per generator: {self.rollouts_per_generator}\n")
        
        for epoch in range(1, self.num_epochs + 1):
            self._print("\n" + "─"*80)
            self._print(f"📚 EPOCH {epoch}/{self.num_epochs}")
            self._print("─"*80 + "\n")
            
            epoch_start_time = datetime.now()
            
            for idx, problem_data in enumerate(training_problems, 1):
                self._print(f"\n{'='*60}")
                self._print(f"Problem {idx}/{len(training_problems)} (Epoch {epoch})")
                self._print('='*60)
                
                self._train_on_problem(problem_data, epoch, idx)
                
                self.experience_manager.training_stats['total_problems'] += 1
            
            self.experience_manager.training_stats['epochs_completed'] = epoch
            
            if save_checkpoint:
                self._save_checkpoint(epoch)
            
            epoch_duration = (datetime.now() - epoch_start_time).total_seconds()
            self._print(f"\n✅ Epoch {epoch} completed in {epoch_duration:.1f}s")
            
            self.experience_manager.print_summary()
        
        self.experience_manager.save_all()
        
        self._print("\n" + "="*80)
        self._print("🎉 Training Complete!")
        self._print("="*80)
        
        self._print_training_summary()
    
    def _train_on_problem(
        self,
        problem_data: Dict[str, Any],
        epoch: int,
        problem_idx: int
    ):
        """
        Train on single problem using per-generator architecture.
        使用每生成器架构在单个问题上训练
        
        Architecture:
        Question → 3 generators (each 3 rollouts) → Critic fuses each → 3 answers → 3 rewards
        """
        problem_text = problem_data['problem']
        ground_truth = problem_data.get('answer', '')
        
        self._print(f"\n📖 Problem: {problem_text[:100]}...")
        self._print(f"✓ Ground Truth: {ground_truth}")
        
        # Step 1: Generate rollouts using GRPO method
        # 步骤1：使用GRPO方法生成rollouts
        self._print(f"\n🔄 Generating rollouts ({self.rollouts_per_generator} per generator)...")
        
        try:
            # Use the GRPO training method
            # 使用GRPO训练方法
            results = self.engine.scaffolder.generate_scaffold_for_grpo_training(
                problem_text=problem_text,
                retrieved_knowledge=[]  # Or get from retriever
            )
            
            if not results:
                self._print("⚠️ No valid results, skipping...")
                return
        
            self._print(f"\n✓ Got {len(results)} fused scaffolds (one per generator)")
            
            # Step 2: Execute and evaluate each result
            # 步骤2：执行并评估每个结果
            self._print(f"\n📊 Evaluating answers...")
            
            evaluations = []
            for result in results:
                agent_id = result['agent_id']
                scaffold = result['scaffold']
                
                # Execute scaffold using LLM Computer to get actual answer
                # 使用LLM计算器执行scaffold获取实际答案
                try:
                    computation_result = self.llm_computer.compute_from_scaffold(
                        causal_scaffold=scaffold,
                        problem_text=problem_text
                    )
                    
                    if computation_result['success']:
                        answer = computation_result['result']
                    else:
                        answer = None
                        self._print(f"  ⚠️ Generator {agent_id}: Computation failed - {computation_result.get('error', 'Unknown error')}")
                except Exception as e:
                    answer = None
                    self._print(f"  ⚠️ Generator {agent_id}: Execution error - {e}")
                
                # Evaluate with problem context for accurate comparison
                # 使用问题上下文进行准确比较
                is_correct = self._compare_answers(answer, ground_truth, problem_text) if answer is not None else False
                
                evaluations.append({
                    'agent_id': agent_id,
                    'scaffold': scaffold,
                    'answer': answer,
                    'is_correct': is_correct,
                    'num_rollouts': result['num_rollouts']
                })
                
                status = "✅ Correct" if is_correct else "❌ Incorrect"
                self._print(f"  Generator {agent_id}: {status} (Answer: {answer})")
            
            # Step 3: Extract and update experiences for each generator
            # 步骤3：为每个生成器提取并更新经验
            # Always extract experiences regardless of success/failure distribution
            # 无论成功/失败分布如何，总是提取经验
            
            correct_count = sum(1 for e in evaluations if e['is_correct'])
            total_count = len(evaluations)
            
            if correct_count == 0:
                self._print(f"\n🧠 Extracting experiences (All failed: 0/{total_count})...")
            elif correct_count == total_count:
                self._print(f"\n🧠 Extracting experiences (All correct: {total_count}/{total_count})...")
            else:
                self._print(f"\n🧠 Extracting experiences (Mixed: {correct_count}/{total_count} correct)...")
            
            self._extract_and_update_experiences(
                problem_data,
                evaluations,
                epoch,
                problem_idx
            )
    
        except Exception as e:
            self._print(f"❌ Error during training: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_answer_comparison_prompt(self) -> str:
        """Load answer comparison prompt from file or use default."""
        from pathlib import Path
        prompt_path = Path("prompts/answer_comparison_prompt.txt")
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Fallback to default prompt
            return """You are a scientific answer verification expert. Determine if two answers are equivalent.

PROBLEM CONTEXT:
{problem_text}

EXPECTED ANSWER: {expected_answer}
PREDICTED ANSWER: {predicted_answer}

Respond with exactly: YES or NO
Then provide a brief reason.

YOUR RESPONSE:"""

    def _compare_answers(self, predicted: str, expected: str, problem_text: str = "") -> bool:
        """
        Compare expected and predicted answers using LLM with problem context.
        使用 LLM 比较预期答案和预测答案（带问题上下文）
        
        This method uses the same robust comparison logic as evaluate_framework.py:
        此方法使用与 evaluate_framework.py 相同的鲁棒比较逻辑：
        - LLM-based comparison with problem context / 基于LLM的比较（带问题上下文）
        - Fallback to rule-based comparison / 降级到基于规则的比较
        - Unit conversion and scientific notation support / 单位转换和科学计数法支持
        
        Args:
            predicted: Predicted answer / 预测答案
            expected: Expected answer / 预期答案
            problem_text: The original problem text for context / 问题原文（用于上下文）
        
        Returns:
            True if answers match, False otherwise / 如果答案匹配返回True，否则返回False
        """
        import re
        
        # False
        if predicted is None:
            return False

        # Use LLM to compare answers with problem context
        try:
            prompt = self.answer_comparison_prompt.format(
                problem_text=problem_text if problem_text else "No context provided",
                expected_answer=expected,
                predicted_answer=predicted
            )

            response = self.llm_client.complete(prompt, temperature=0.0)

            # Parse response - look for YES or NO
            response_upper = response.strip().upper()

            if response_upper.startswith("YES"):
                if self.verbose:
                    self._print(f"  ✓ LLM Answer Comparison: YES")
                return True
            elif response_upper.startswith("NO"):
                if self.verbose:
                    self._print(f"  ✗ LLM Answer Comparison: NO")
                return False
            else:
                # If LLM response is unclear, fallback to string matching
                if self.verbose:
                    self._print(f"  ⚠ LLM response unclear, using fallback comparison")
                return self._fallback_compare(expected, predicted)
                
        except Exception as e:
            # If LLM fails, use fallback comparison
            if self.verbose:
                self._print(f"  ⚠ LLM comparison failed: {e}, using fallback")
            return self._fallback_compare(expected, predicted)
    
    def _fallback_compare(self, expected: str, predicted: Any) -> bool:
        """
        Fallback comparison method with enhanced unit and scientific notation handling.
        带增强单位和科学计数法处理的备用比较方法。
        
        This is the same robust fallback used in evaluate_framework.py.
        这是 evaluate_framework.py 中使用的相同鲁棒备用方法。
        """
        import re
        
        expected_str = str(expected).strip().lower()
        predicted_str = str(predicted).strip().lower()

        # Remove LaTeX, brackets, quotes
        expected_str = re.sub(r'[\$\\{}\[\]\'\"]', '', expected_str)
        predicted_str = re.sub(r'[\$\\{}\[\]\'\"]', '', predicted_str)

        # Exact match (after basic cleanup)
        if expected_str == predicted_str:
            return True

        # Extract numerical values (handles scientific notation and units)
        def extract_number_and_unit(s):
            """Extract numerical value and unit from string, handling scientific notation"""
            s = s.strip()
            
            # Handle scientific notation: 2×10^5, 2e5, 2*10^5
            scientific_patterns = [
                r'([\d.]+)\s*[×x*]\s*10\s*\^\s*([+-]?\d+)\s*([a-zA-Z/°²³]+)?',  # 2×10^5 or 2*10^5 with optional unit
                r'([\d.]+)\s*[eE]\s*([+-]?\d+)\s*([a-zA-Z/°²³]+)?',              # 2e5 or 2E5 with optional unit
            ]
            
            for pattern in scientific_patterns:
                match = re.search(pattern, s)
                if match:
                    base = float(match.group(1))
                    exponent = float(match.group(2))
                    unit = match.group(3) if len(match.groups()) >= 3 else None
                    value = base * (10 ** exponent)
                    return (value, unit)
            
            # Extract number and unit: "30", "30 m/s", "30m/s", "30.5 kg", "6 kW"
            num_unit_match = re.search(r'^([+-]?[\d.]+)\s*([a-zA-Z/°²³]+)?', s)
            if num_unit_match:
                value = float(num_unit_match.group(1))
                unit = num_unit_match.group(2)
                return (value, unit)
            
            return (None, None)
        
        def normalize_unit_value(value, unit):
            """Convert to base units (e.g., kW -> W, km -> m)"""
            if value is None:
                return None
            
            if unit is None:
                return value
            
            unit_lower = unit.lower()
            
            # Power conversions
            if unit_lower in ['kw', 'kilowatt']:
                return value * 1000  # kW to W
            elif unit_lower in ['mw', 'megawatt']:
                return value * 1000000  # MW to W
            
            # Energy conversions
            elif unit_lower in ['kj', 'kilojoule']:
                return value * 1000  # kJ to J
            elif unit_lower in ['mj', 'megajoule']:
                return value * 1000000  # MJ to J
            
            # Distance conversions
            elif unit_lower in ['km', 'kilometer']:
                return value * 1000  # km to m
            elif unit_lower in ['cm', 'centimeter']:
                return value / 100  # cm to m
            elif unit_lower in ['mm', 'millimeter']:
                return value / 1000  # mm to m
            
            # Mass conversions
            elif unit_lower in ['g', 'gram']:
                return value / 1000  # g to kg
            elif unit_lower in ['ton', 'tonne']:
                return value * 1000  # ton to kg
            
            # Time conversions
            elif unit_lower in ['min', 'minute']:
                return value * 60  # min to s
            elif unit_lower in ['h', 'hour', 'hr']:
                return value * 3600  # hour to s
            
            # Pressure conversions
            elif unit_lower in ['kpa', 'kilopascal']:
                return value * 1000  # kPa to Pa
            elif unit_lower in ['mpa', 'megapascal']:
                return value * 1000000  # MPa to Pa
            
            # If no conversion needed, return original value
            return value

        # Try numerical comparison with unit conversion
        try:
            expected_num, expected_unit = extract_number_and_unit(expected_str)
            predicted_num, predicted_unit = extract_number_and_unit(predicted_str)
            
            if expected_num is not None and predicted_num is not None:
                # Normalize units to base units (e.g., kW -> W, km -> m)
                expected_normalized = normalize_unit_value(expected_num, expected_unit)
                predicted_normalized = normalize_unit_value(predicted_num, predicted_unit)
                
                # Compare normalized values
                if expected_normalized is not None and predicted_normalized is not None:
                    # Use relative tolerance for large numbers, absolute for small
                    if abs(expected_normalized) > 1e-6:
                        relative_diff = abs(expected_normalized - predicted_normalized) / abs(expected_normalized)
                        if relative_diff < 1e-4:  # 0.01% relative tolerance
                            return True
                    
                    # Absolute tolerance
                    if abs(expected_normalized - predicted_normalized) < 1e-6:
                        return True
        except Exception as e:
            if self.verbose:
                self._print(f"    ⚠ Fallback comparison error: {e}")
            pass

        # Remove all spaces and try exact match again
        expected_clean = re.sub(r'\s+', '', expected_str)
        predicted_clean = re.sub(r'\s+', '', predicted_str)
        
        if expected_clean == predicted_clean:
            return True

        return False
    
    def _extract_and_update_experiences(
        self,
        problem_data: Dict[str, Any],
        evaluations: List[Dict[str, Any]],
        epoch: int,
        problem_idx: int
    ):
        """
        Extract experiences for each generator individually.
        为每个生成器单独提取经验
        
        Core principle: we update each generator's experience based on 
        its own performance, not mixing all together.
        
        核心原则：我们根据每个生成器自己的表现更新其经验，
        而不是混在一起。
        """
        problem_text = problem_data['problem']
        ground_truth = problem_data.get('answer', '')
        
        # Update experience for each generator
        # 为每个生成器更新经验
        for eval_result in evaluations:
            agent_id = eval_result['agent_id']
            is_correct = eval_result['is_correct']
            answer = eval_result['answer']
            num_rollouts = eval_result['num_rollouts']
            
            # Get current experiences for this generator
            # 获取这个生成器的当前经验
            agent_type = f'generator_{agent_id}'
            current_exp = self.experience_manager.get_experiences_for_agent(
                agent_type,
                include_shared=False,
                format_as_prompt=False
            )
            
            current_exp_str = "\n".join([
                f"{exp.id}: {exp.content}" for exp in current_exp
            ]) if current_exp else "No experiences yet"
            
            # Construct prompt for this generator
            # 为这个生成器构造提示
            result_str = "Correct ✓" if is_correct else "Incorrect ✗"
            
            prompt = self.generator_advantage_prompt.format(
                generator_id=agent_id,
                problem=problem_text,
                ground_truth=ground_truth,
                num_rollouts=num_rollouts,
                final_answer=answer,
                result=result_str,
                current_experiences=current_exp_str
            )
            
            # Extract experiences for this generator
            # 为这个生成器提取经验
            try:
                self._print(f"\n  📝 Extracting experiences for Generator {agent_id}...")
                
                response = self.llm_client.complete(prompt, temperature=0.3)
                operations = self._parse_operations(response)
                
                if operations:
                    self._apply_operations(operations, agent_type)
                    self._print(f"    ✓ Updated Generator {agent_id}'s experiences")
                else:
                    self._print(f"    ℹ No updates for Generator {agent_id}")
                    
            except Exception as e:
                self._print(f"    ⚠️ Error updating Generator {agent_id}: {e}")
        
        # Also update critic experience (based on fusion success rate)
        # 同时更新critic经验（基于融合成功率）
        self._update_critic_experience(problem_data, evaluations)
    
    def _update_critic_experience(
        self,
        problem_data: Dict[str, Any],
        evaluations: List[Dict[str, Any]]
    ):
        """
        Update critic's experience based on fusion performance.
        根据融合表现更新critic经验
        """
        self._print(f"\n  🧠 Analyzing Critic's fusion performance...")
        
        # Build critic performance summary
        # 构建critic表现总结
        critic_perf_lines = []
        for eval_result in evaluations:
            agent_id = eval_result['agent_id']
            is_correct = eval_result['is_correct']
            status = "Successful" if is_correct else "Failed"
            critic_perf_lines.append(
                f"- Generator {agent_id}: {eval_result['num_rollouts']} rollouts → {status}"
            )
        
        critic_performance = "\n".join(critic_perf_lines)
        
        # Get current critic experiences
        # 获取当前critic经验
        current_exp = self.experience_manager.get_experiences_for_agent(
            'critic',
            include_shared=False,
            format_as_prompt=False
        )
        
        current_exp_str = "\n".join([
            f"{exp.id}: {exp.content}" for exp in current_exp
        ]) if current_exp else "No experiences yet"
        
        prompt = self.critic_advantage_prompt.format(
            problem=problem_data['problem'],
            ground_truth=problem_data.get('answer', ''),
            critic_performance=critic_performance,
            current_experiences=current_exp_str
        )
        
        try:
            response = self.llm_client.complete(prompt, temperature=0.3)
            operations = self._parse_operations(response)
            
            if operations:
                self._apply_operations(operations, 'critic')
                self._print(f"    ✓ Updated Critic's experiences")
            else:
                self._print(f"    ℹ No updates for Critic")
            
        except Exception as e:
            self._print(f"    ⚠️ Error updating Critic: {e}")
    
    def _parse_operations(self, response: str) -> List[Dict[str, Any]]:
        """Parse operations from LLM response."""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                return data.get('operations', [])
        except Exception as e:
            self._print(f"⚠️ Error parsing operations: {e}")
        
        return []
    
    def _apply_operations(
        self,
        operations: List[Dict[str, Any]],
        agent_type: str
    ):
        """Apply experience operations."""
        for op in operations:
            action = op.get('action', '').lower()
            
            if action == 'add':
                content = op.get('content', '')
                category = op.get('category', 'general')
                
                if content:
                    self.experience_manager.add_experience(
                        agent_type=agent_type,
                        content=content,
                        category=category,
                        save=False
                    )
            
            elif action == 'modify':
                exp_id = op.get('experience_id', '')
                new_content = op.get('new_content', '')
                
                if exp_id and new_content:
                    self.experience_manager.modify_experience(
                        exp_id=exp_id,
                        new_content=new_content,
                        save=False
                    )
            
            elif action == 'delete':
                exp_id = op.get('experience_id', '')
                
                if exp_id:
                    self.experience_manager.delete_experience(
                        exp_id=exp_id,
                        save=False
                    )
        
        self.experience_manager.save_all()
    
    def _save_checkpoint(self, epoch: int):
        """Save training checkpoint."""
        checkpoint_dir = Path("checkpoints/grpo")
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint_path = checkpoint_dir / f"epoch_{epoch}.json"
        
        self.experience_manager.export_for_deployment(str(checkpoint_path))
        
        self._print(f"💾 Checkpoint saved: {checkpoint_path}")
    
    def _print_training_summary(self):
        """Print training summary."""
        stats = self.experience_manager.get_statistics()
        
        print("\n" + "="*80)
        print("📊 TRAINING SUMMARY")
        print("="*80)
        
        print(f"\n✅ Problems processed: {stats['training_stats']['total_problems']}")
        print(f"✅ Experiences added: {stats['training_stats']['total_experiences_added']}")
        print(f"✏️ Experiences modified: {stats['training_stats']['total_experiences_modified']}")
        print(f"🗑️ Experiences deleted: {stats['training_stats']['total_experiences_deleted']}")
        print(f"🔄 Epochs completed: {stats['training_stats']['epochs_completed']}")
        
        print(f"\n📚 Final Experience Counts:")
        for agent_type, count in stats['experience_counts'].items():
            print(f"   - {agent_type}: {count} experiences")
        
        print("\n" + "="*80)


# Example usage
if __name__ == "__main__":
    print("Training-Free GRPO Trainer (Per-Generator Architecture)")
    print("训练自由GRPO训练器（每生成器架构）")
    print("\nKey features:")
    print("- Each generator produces multiple rollouts")
    print("- Critic fuses each generator's rollouts separately")
    print("- Get 3 final answers (one per generator)")
    print("- Update each LLM's experience individually")

