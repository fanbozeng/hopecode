"""
DAG Enhancement Pipeline Module
DAG增强流水线模块

This module orchestrates the three-stage DAG enhancement process:
Stage 1: Domain Expert Review & Correction (actively fixes math/physics errors)
Stage 2: RAG Knowledge Enhancement (injects relevant domain knowledge)
Stage 3: Causal Structure Optimization (optimizes DAG structure using causal principles)

本模块协调三阶段DAG增强流程：
阶段1：领域专家审查与修正（主动修复数学/物理错误）
阶段2：RAG知识增强（注入相关领域知识）
阶段3：因果结构优化（使用因果原理优化DAG结构）
"""

from typing import Dict, List, Any, Optional, Tuple
from engine.domain_expert_reviewer import DomainExpertReviewer, ProblemType
from engine.rag_knowledge_enhancer import RAGKnowledgeEnhancer
from engine.causal_structure_optimizer import CausalStructureOptimizer


class DAGEnhancementPipeline:
    """
    Pipeline for orchestrating multi-stage DAG enhancement.
    协调多阶段DAG增强的流水线
    
    This class provides a unified interface for the complete enhancement process,
    managing data flow between stages and collecting comprehensive reports.
    
    本类为完整的增强流程提供统一接口，管理阶段间的数据流并收集综合报告。
    """
    
    def __init__(
        self,
        expert_reviewer: Optional[DomainExpertReviewer] = None,
        rag_enhancer: Optional[RAGKnowledgeEnhancer] = None,
        structure_optimizer: Optional[CausalStructureOptimizer] = None,
        verbose: bool = True
    ):
        """
        Initialize DAG enhancement pipeline.
        
        Args:
            expert_reviewer: DomainExpertReviewer instance (Stage 1)
            rag_enhancer: RAGKnowledgeEnhancer instance (Stage 2)
            structure_optimizer: CausalStructureOptimizer instance (Stage 3)
            verbose: Whether to print progress
        """
        self.expert_reviewer = expert_reviewer
        self.rag_enhancer = rag_enhancer
        self.structure_optimizer = structure_optimizer
        self.verbose = verbose
        
        if self.verbose:
            stages = []
            if self.expert_reviewer:
                stages.append("Expert Review")
            if self.rag_enhancer:
                stages.append("RAG Enhancement")
            if self.structure_optimizer:
                stages.append("Structure Optimization")
            
            print(f"✓ DAGEnhancementPipeline initialized with {len(stages)} stages: {', '.join(stages)}")
    
    def _print(self, message: str, **kwargs):
        """Conditional print"""
        if self.verbose:
            print(message, **kwargs)
    
    def enhance_dag(
        self,
        fixed_dag: Dict[str, Any],
        problem_text: str,
        problem_type: Optional[ProblemType] = None,
        skip_stages: Optional[List[str]] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Run complete DAG enhancement pipeline.
        运行完整的DAG增强流水线
        
        Args:
            fixed_dag: Fixed DAG from Step1 (multi-agent scaffolding)
            problem_text: Original problem description
            problem_type: Problem type (math/physics/general), auto-detected if None
            skip_stages: Optional list of stages to skip ['expert', 'rag', 'structure']
        
        Returns:
            Tuple of (enhanced_dag, comprehensive_report)
        """
        skip_stages = skip_stages or []
        
        self._print("=" * 60)
        self._print("🚀 Starting DAG Enhancement Pipeline")
        self._print("=" * 60)
        
        # Initialize tracking
        current_dag = fixed_dag
        enhancement_report = {
            'pipeline_status': 'in_progress',
            'stages_run': [],
            'expert_review': {},
            'rag_enhancement': {},
            'structure_optimization': {},
            'summary': {}
        }
        
        try:
            # Stage 1: Domain Expert Review & Correction
            # 阶段1：领域专家审查与修正
            # Actively fixes math/physics errors and returns a corrected DAG
            # 主动修复数学/物理错误并返回修正后的DAG
            if 'expert' not in skip_stages and self.expert_reviewer:
                self._print("\n📋 Stage 1/3: Domain Expert Review & Correction")
                self._print("-" * 60)
                current_dag, expert_report = self.expert_reviewer.review_dag(
                    current_dag, problem_text, problem_type
                )
                enhancement_report['expert_review'] = expert_report
                enhancement_report['stages_run'].append('expert_review')
            else:
                self._print("\n⏭️  Stage 1/3: Expert Review & Correction (Skipped)")
                enhancement_report['expert_review'] = {'status': 'skipped'}
            
            # Stage 2: RAG Knowledge Enhancement
            if 'rag' not in skip_stages and self.rag_enhancer:
                self._print("\n📋 Stage 2/3: RAG Knowledge Enhancement")
                self._print("-" * 60)
                current_dag, rag_report = self.rag_enhancer.enhance_dag_with_knowledge(
                    current_dag, problem_text
                )
                enhancement_report['rag_enhancement'] = rag_report
                enhancement_report['stages_run'].append('rag_enhancement')
            else:
                self._print("\n⏭️  Stage 2/3: RAG Enhancement (Skipped)")
                enhancement_report['rag_enhancement'] = {'status': 'skipped'}
            
            # Stage 3: Causal Structure Optimization
            if 'structure' not in skip_stages and self.structure_optimizer:
                self._print("\n📋 Stage 3/3: Causal Structure Optimization")
                self._print("-" * 60)
                current_dag, structure_report = self.structure_optimizer.optimize_causal_structure(
                    current_dag, problem_text
                )
                enhancement_report['structure_optimization'] = structure_report
                enhancement_report['stages_run'].append('structure_optimization')
            else:
                self._print("\n⏭️  Stage 3/3: Structure Optimization (Skipped)")
                enhancement_report['structure_optimization'] = {'status': 'skipped'}
            
            # Generate summary
            enhancement_report['summary'] = self._generate_summary(enhancement_report)
            enhancement_report['pipeline_status'] = 'success'
            
            self._print("\n" + "=" * 60)
            self._print("✅ DAG Enhancement Pipeline Completed")
            self._print("=" * 60)
            self._print_summary(enhancement_report['summary'])
            
            return current_dag, enhancement_report
        
        except Exception as e:
            self._print(f"\n❌ Pipeline failed: {str(e)}")
            enhancement_report['pipeline_status'] = 'failed'
            enhancement_report['error'] = str(e)
            return current_dag, enhancement_report
    
    def _generate_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summary statistics from enhancement report.
        从增强报告生成汇总统计
        
        Args:
            report: Full enhancement report
        
        Returns:
            Summary dictionary with key metrics
        """
        summary = {
            'stages_completed': len(report['stages_run']),
            'total_stages': 3
        }
        
        # Expert review summary
        expert = report.get('expert_review', {})
        summary['expert_issues_found'] = len(expert.get('issues', []))
        summary['expert_corrections_applied'] = len(expert.get('corrections', []))
        
        # RAG enhancement summary
        rag = report.get('rag_enhancement', {})
        summary['knowledge_gaps_identified'] = len(rag.get('gaps_identified', []))
        summary['knowledge_items_retrieved'] = len(rag.get('knowledge_retrieved', []))
        summary['rag_nodes_added'] = rag.get('nodes_added', 0)
        
        # Structure optimization summary
        structure = report.get('structure_optimization', {})
        summary['chains_found'] = structure.get('num_chains', 0)
        summary['forks_found'] = structure.get('num_forks', 0)
        summary['colliders_found'] = structure.get('num_colliders', 0)
        summary['is_valid_dag'] = structure.get('is_dag', True)
        summary['structural_issues'] = len(structure.get('structural_issues', []))
        
        # Overall quality score (heuristic)
        quality_score = self._compute_quality_score(summary, report)
        summary['quality_score'] = quality_score
        
        return summary
    
    def _compute_quality_score(
        self,
        summary: Dict[str, Any],
        report: Dict[str, Any]
    ) -> float:
        """
        Compute overall quality score for enhanced DAG.
        计算增强后DAG的整体质量分数
        
        This is a heuristic score based on:
        - Number of issues fixed
        - Knowledge enrichment
        - Structural soundness
        
        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.5  # Base score
        
        # Bonus for fixing expert issues
        corrections = summary.get('expert_corrections_applied', 0)
        if corrections > 0:
            score += min(0.2, corrections * 0.05)
        
        # Bonus for knowledge enrichment
        knowledge_added = summary.get('knowledge_items_retrieved', 0)
        if knowledge_added > 0:
            score += min(0.15, knowledge_added * 0.03)
        
        # Bonus for valid DAG structure
        if summary.get('is_valid_dag', False):
            score += 0.1
        
        # Bonus for finding causal patterns
        patterns = (
            summary.get('chains_found', 0) +
            summary.get('forks_found', 0) +
            summary.get('colliders_found', 0)
        )
        if patterns > 0:
            score += min(0.1, patterns * 0.02)
        
        # Penalty for unresolved structural issues
        issues = summary.get('structural_issues', 0)
        if issues > 0:
            score -= min(0.15, issues * 0.05)
        
        return max(0.0, min(1.0, score))
    
    def _print_summary(self, summary: Dict[str, Any]):
        """Print enhancement summary in a readable format"""
        self._print("\n📊 Enhancement Summary:")
        self._print(f"  • Stages completed: {summary['stages_completed']}/{summary['total_stages']}")
        self._print(f"  • Expert corrections: {summary['expert_corrections_applied']}")
        self._print(f"  • Knowledge items added: {summary['knowledge_items_retrieved']}")
        self._print(f"  • Causal patterns: {summary['chains_found']} chains, {summary['forks_found']} forks, {summary['colliders_found']} colliders")
        self._print(f"  • Valid DAG: {summary['is_valid_dag']}")
        self._print(f"  • Quality score: {summary['quality_score']:.2f}")
    
    # Optional: Individual stage methods for more control
    
    def step_1_expert_review(
        self,
        dag: Dict[str, Any],
        problem_text: str,
        problem_type: Optional[ProblemType] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Run only Stage 1: Expert Review"""
        if not self.expert_reviewer:
            raise ValueError("Expert reviewer not initialized")
        return self.expert_reviewer.review_dag(dag, problem_text, problem_type)
    
    def step_2_rag_enhancement(
        self,
        dag: Dict[str, Any],
        problem_text: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Run only Stage 2: RAG Enhancement"""
        if not self.rag_enhancer:
            raise ValueError("RAG enhancer not initialized")
        return self.rag_enhancer.enhance_dag_with_knowledge(dag, problem_text)
    
    def step_3_structure_optimization(
        self,
        dag: Dict[str, Any],
        problem_text: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Run only Stage 3: Structure Optimization"""
        if not self.structure_optimizer:
            raise ValueError("Structure optimizer not initialized")
        return self.structure_optimizer.optimize_causal_structure(dag, problem_text)




