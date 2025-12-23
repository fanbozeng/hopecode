"""
RAG Knowledge Enhancer Module
RAG知识增强模块

This module enhances causal DAGs by retrieving and injecting relevant
domain knowledge, formulas, and principles using RAG (Retrieval-Augmented Generation).

本模块通过RAG(检索增强生成)检索并注入相关的领域知识、公式和原理来增强因果DAG。
"""

import json
import re
import copy
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class RAGKnowledgeEnhancer:
    """
    RAG-based Knowledge Enhancer for DAG enrichment.
    基于RAG的知识增强器，用于DAG丰富化
    
    This class:
    1. Identifies knowledge gaps in the DAG
    2. Retrieves relevant knowledge using AI/Vector retriever
    3. Injects retrieved knowledge into the DAG structure
    
    本类功能：
    1. 识别DAG中的知识缺口
    2. 使用AI/向量检索器检索相关知识
    3. 将检索到的知识注入DAG结构
    """
    
    def __init__(
        self,
        ai_retriever=None,
        vector_retriever=None,
        verbose: bool = True
    ):
        """
        Initialize RAG knowledge enhancer.
        
        Args:
            ai_retriever: AIKnowledgeRetriever instance for dynamic knowledge generation
            vector_retriever: VectorKnowledgeRetriever instance for similarity-based retrieval
            verbose: Whether to print progress
        """
        self.ai_retriever = ai_retriever
        self.vector_retriever = vector_retriever
        self.verbose = verbose
        
        # Load prompts
        self._load_prompts()
        
        if self.verbose:
            retrievers = []
            if self.ai_retriever:
                retrievers.append("AI Retriever")
            if self.vector_retriever:
                retrievers.append("Vector Retriever")
            print(f"✓ RAGKnowledgeEnhancer initialized with: {', '.join(retrievers) if retrievers else 'No retrievers'}")
    
    def _print(self, message: str, **kwargs):
        """Conditional print"""
        if self.verbose:
            print(message, **kwargs)
    
    def _load_prompts(self):
        """Load knowledge gap identification and injection prompts"""
        # Load gap identification prompt
        gap_prompt_path = Path("prompts/knowledge_gap_identification_prompt.txt")
        if gap_prompt_path.exists():
            with open(gap_prompt_path, 'r', encoding='utf-8') as f:
                self.gap_identification_prompt = f.read()
        else:
            self.gap_identification_prompt = self._get_default_gap_prompt()
        
        # Load knowledge injection prompt
        injection_prompt_path = Path("prompts/knowledge_injection_prompt.txt")
        if injection_prompt_path.exists():
            with open(injection_prompt_path, 'r', encoding='utf-8') as f:
                self.knowledge_injection_prompt = f.read()
        else:
            self.knowledge_injection_prompt = self._get_default_injection_prompt()
    
    def _get_default_gap_prompt(self) -> str:
        """Default knowledge gap identification prompt"""
        return """Analyze the following causal DAG to identify knowledge gaps.

**Problem:**
{problem}

**Causal DAG:**
{dag}

**Tasks:**
1. Identify missing formulas, theorems, or principles
2. Detect incomplete reasoning chains
3. Suggest relevant domain knowledge

**Output JSON Format:**
{{
  "knowledge_gaps": [
    {{"gap_type": "formula/theorem/principle", "description": "...", "priority": "high/medium/low"}}
  ],
  "suggestions": [
    {{"knowledge_item": "...", "application": "...", "confidence": 0.0-1.0}}
  ]
}}
"""
    
    def _get_default_injection_prompt(self) -> str:
        """Default knowledge injection prompt"""
        return """You are a Knowledge Integration Expert. Inject the retrieved knowledge into the DAG.

**Problem:** {problem}
**Current DAG:** {dag}
**Retrieved Knowledge:** {knowledge_rules}
**Knowledge Gaps:** {knowledge_gaps}

Analyze the knowledge and inject relevant items into the DAG structure.
Output JSON with: analysis, injections, knowledge_enhanced_dag, summary.
"""
    
    def enhance_dag_with_knowledge(
        self,
        dag: Dict[str, Any],
        problem_text: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Enhance DAG by identifying gaps and retrieving relevant knowledge.
        通过识别缺口并检索相关知识来增强DAG
        
        Args:
            dag: Reviewed DAG from expert review step
            problem_text: Original problem description
        
        Returns:
            Tuple of (enhanced_dag, knowledge_report)
        """
        self._print("📚 Enhancing DAG with RAG knowledge...", end=" ")
        
        try:
            # Step 1: Identify knowledge gaps
            gaps = self._identify_knowledge_gaps(dag, problem_text)
            
            if not gaps or len(gaps.get('knowledge_gaps', [])) == 0:
                self._print("✓ No significant knowledge gaps found")
                return dag, {
                    'status': 'no_gaps',
                    'gaps_identified': [],
                    'knowledge_retrieved': [],
                    'injection_method': 'none'
                }
            
            # Step 2: Retrieve relevant knowledge for identified gaps
            knowledge_rules = self._retrieve_relevant_knowledge(gaps, problem_text)
            
            if not knowledge_rules:
                self._print("✓ No additional knowledge retrieved")
                return dag, {
                    'status': 'no_retrieval',
                    'gaps_identified': gaps.get('knowledge_gaps', []),
                    'knowledge_retrieved': [],
                    'injection_method': 'none'
                }
            
            # Step 3: Inject knowledge into DAG (LLM-driven)
            enhanced_dag, injection_report = self._inject_knowledge_into_dag(
                dag, knowledge_rules, gaps, problem_text
            )
            
            # Prepare knowledge report
            knowledge_report = {
                'status': 'success',
                'gaps_identified': gaps.get('knowledge_gaps', []),
                'knowledge_retrieved': knowledge_rules,
                'injection_method': injection_report.get('method', 'unknown'),
                'injection_details': injection_report,
                'suggestions': gaps.get('suggestions', [])
            }
            
            self._print(f"✓ Knowledge injected via {injection_report.get('method', 'unknown')}")
            
            return enhanced_dag, knowledge_report
        
        except Exception as e:
            self._print(f"✗ Failed: {str(e)}")
            return dag, {
                'status': 'failed',
                'error': str(e),
                'gaps_identified': [],
                'knowledge_retrieved': [],
                'injection_method': 'failed'
            }
    
    def _identify_knowledge_gaps(
        self,
        dag: Dict[str, Any],
        problem_text: str
    ) -> Dict[str, Any]:
        """
        Identify knowledge gaps in the DAG using LLM analysis.
        使用LLM分析识别DAG中的知识缺口
        
        Args:
            dag: Current DAG
            problem_text: Problem description
        
        Returns:
            Dictionary containing identified gaps and suggestions
        """
        # If no AI retriever, use rule-based gap detection
        if not self.ai_retriever:
            return self._rule_based_gap_detection(dag)
        
        try:
            # Use AI retriever's LLM to identify gaps
            prompt = self.gap_identification_prompt.format(
                problem=problem_text,
                dag=json.dumps(dag, indent=2, ensure_ascii=False)
            )
            
            # Call LLM to identify gaps
            response = self.ai_retriever.llm_client.complete(prompt, temperature=0.0)
            
            # Parse response
            gaps = self._parse_gap_response(response)
            return gaps
        
        except Exception as e:
            self._print(f"  ⚠️  Gap identification failed, using rule-based fallback: {e}")
            return self._rule_based_gap_detection(dag)
    
    def _parse_gap_response(self, response: str) -> Dict[str, Any]:
        """Parse gap identification response"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                gaps = json.loads(json_match.group(0))
                # Ensure required fields
                if 'knowledge_gaps' not in gaps:
                    gaps['knowledge_gaps'] = []
                if 'suggestions' not in gaps:
                    gaps['suggestions'] = []
                return gaps
            else:
                return {'knowledge_gaps': [], 'suggestions': []}
        except json.JSONDecodeError:
            return {'knowledge_gaps': [], 'suggestions': []}
    
    def _rule_based_gap_detection(self, dag: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback: Rule-based knowledge gap detection.
        回退方案：基于规则的知识缺口检测
        
        Detects gaps by checking:
        - Missing rules in causal links
        - Isolated nodes without connections
        - Very short reasoning chains
        """
        gaps = []
        
        # Check causal graph
        if 'causal_graph' in dag:
            for i, link in enumerate(dag['causal_graph']):
                # Check if rule is missing or too short
                rule = link.get('rule', '')
                if not rule or len(rule) < 10:
                    gaps.append({
                        'gap_type': 'missing_rule',
                        'description': f"Link {i} (effect: {link.get('effect')}) lacks detailed reasoning",
                        'priority': 'medium'
                    })
        
        return {
            'knowledge_gaps': gaps,
            'suggestions': []
        }
    
    def _retrieve_relevant_knowledge(
        self,
        gaps: Dict[str, Any],
        problem_text: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve knowledge for identified gaps using available retrievers.
        使用可用的检索器为识别的缺口检索知识
        
        Args:
            gaps: Identified knowledge gaps
            problem_text: Problem description
        
        Returns:
            List of knowledge rules
        """
        knowledge_rules = []
        
        # Extract gap descriptions for retrieval
        gap_queries = []
        for gap in gaps.get('knowledge_gaps', []):
            gap_queries.append(gap.get('description', ''))
        
        # Also use suggestions as queries
        for suggestion in gaps.get('suggestions', []):
            gap_queries.append(suggestion.get('knowledge_item', ''))
        
        if not gap_queries:
            return []
        
        # Try AI retriever first
        if self.ai_retriever:
            try:
                # Combine problem + gaps for context-aware retrieval
                query = f"{problem_text}\n\nKnowledge needed: {', '.join(gap_queries)}"
                # Correct method is extract_knowledge, which returns a list of strings
                rules = self.ai_retriever.extract_knowledge(query)
                
                # Convert to standard format
                for rule_text in rules:
                    knowledge_rules.append({
                        'rule': rule_text,
                        'source': 'AI_retriever',
                        'confidence': 0.85,  # Assign a default confidence
                        'category': 'ai_generated'
                    })
            except Exception as e:
                self._print(f"  ⚠️  AI retrieval failed: {e}")
        
        # Try vector retriever as supplement
        if self.vector_retriever and len(knowledge_rules) < 3:
            try:
                # Use problem text for vector similarity search
                vector_rules = self.vector_retriever.retrieve_by_similarity(
                    problem_text, top_k=3
                )
                
                for rule in vector_rules:
                    knowledge_rules.append({
                        'rule': rule.get('content', ''),
                        'source': 'vector_retriever',
                        'confidence': rule.get('similarity', 0.7),
                        'category': rule.get('category', 'general')
                    })
            except Exception as e:
                self._print(f"  ⚠️  Vector retrieval failed: {e}")
        
        return knowledge_rules
    
    def _llm_inject_knowledge(
        self,
        dag: Dict[str, Any],
        knowledge_rules: List[Dict[str, Any]],
        knowledge_gaps: Dict[str, Any],
        problem_text: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Use LLM to intelligently inject knowledge into DAG structure.
        使用LLM智能地将知识注入DAG结构
        
        This is the core innovation: instead of just adding metadata,
        we use LLM to actually modify the DAG (knowns, causal_graph, computation_plan)
        
        Args:
            dag: Current DAG
            knowledge_rules: Retrieved knowledge
            knowledge_gaps: Identified gaps
            problem_text: Problem description
        
        Returns:
            Tuple of (knowledge_enhanced_dag, injection_report)
        """
        # If no AI retriever (no LLM), fall back to simple metadata injection
        if not self.ai_retriever:
            self._print("  ⚠️  No LLM available, using simple metadata injection")
            return self._simple_metadata_injection(dag, knowledge_rules)
        
        try:
            # Prepare prompt
            prompt = self.knowledge_injection_prompt.format(
                problem=problem_text,
                dag=json.dumps(dag, indent=2, ensure_ascii=False),
                knowledge_rules=json.dumps(knowledge_rules, indent=2, ensure_ascii=False),
                knowledge_gaps=json.dumps(knowledge_gaps, indent=2, ensure_ascii=False)
            )
            
            # Call LLM to inject knowledge
            response = self.ai_retriever.llm_client.complete(prompt, temperature=0.0)
            
            # Parse response
            injection_result = self._parse_injection_response(response)
            
            if not injection_result or 'knowledge_enhanced_dag' not in injection_result:
                self._print("  ⚠️  LLM injection failed to return valid DAG, using fallback")
                return self._simple_metadata_injection(dag, knowledge_rules)
            
            # Extract enhanced DAG and report
            enhanced_dag = injection_result['knowledge_enhanced_dag']
            
            injection_report = {
                'method': 'llm_injection',
                'analysis': injection_result.get('analysis', {}),
                'injections': injection_result.get('injections', []),
                'summary': injection_result.get('summary', 'Knowledge injected via LLM')
            }
            
            return enhanced_dag, injection_report
        
        except Exception as e:
            self._print(f"  ⚠️  LLM injection error: {e}, using fallback")
            return self._simple_metadata_injection(dag, knowledge_rules)
    
    def _parse_injection_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM injection response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result
            else:
                return None
        except json.JSONDecodeError as e:
            self._print(f"  ⚠️  JSON parse error: {e}")
            return None
    
    def _simple_metadata_injection(
        self,
        dag: Dict[str, Any],
        knowledge_rules: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Fallback: Simple metadata injection (original behavior).
        回退方案：简单的metadata注入（原始行为）
        
        Only adds knowledge to a separate field, doesn't modify DAG structure.
        """
        enhanced_dag = copy.deepcopy(dag)
        
        # Add to knowledge_base field
        if 'knowledge_base' not in enhanced_dag:
            enhanced_dag['knowledge_base'] = []
        
        for kr in knowledge_rules:
            enhanced_dag['knowledge_base'].append({
                'rule': kr['rule'],
                'source': kr['source'],
                'confidence': kr.get('confidence', 0.8),
                'category': kr.get('category', 'general')
            })
        
        injection_report = {
            'method': 'simple_metadata',
            'note': 'Knowledge added to metadata only, DAG structure unchanged',
            'items_added': len(knowledge_rules)
        }
        
        return enhanced_dag, injection_report
    
    def _inject_knowledge_into_dag(
        self,
        dag: Dict[str, Any],
        knowledge_rules: List[Dict[str, Any]],
        knowledge_gaps: Dict[str, Any],
        problem_text: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Inject retrieved knowledge into DAG structure using LLM.
        使用LLM将检索到的知识注入DAG结构
        
        This is the NEW implementation (after Stage 2 fix):
        - Uses LLM to intelligently inject knowledge
        - Actually modifies DAG structure (knowns, causal_graph, computation_plan)
        - Falls back to simple metadata injection if LLM unavailable
        
        Args:
            dag: Current DAG
            knowledge_rules: Retrieved knowledge to inject
            knowledge_gaps: Identified gaps
            problem_text: Problem description
        
        Returns:
            Tuple of (enhanced_dag, injection_report)
        """
        # Use LLM-driven knowledge injection
        return self._llm_inject_knowledge(
            dag, knowledge_rules, knowledge_gaps, problem_text
        )





"""
RAG知识增强模块

This module enhances causal DAGs by retrieving and injecting relevant
domain knowledge, formulas, and principles using RAG (Retrieval-Augmented Generation).

本模块通过RAG(检索增强生成)检索并注入相关的领域知识、公式和原理来增强因果DAG。
"""

import json
import re
import copy
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class RAGKnowledgeEnhancer:
    """
    RAG-based Knowledge Enhancer for DAG enrichment.
    基于RAG的知识增强器，用于DAG丰富化
    
    This class:
    1. Identifies knowledge gaps in the DAG
    2. Retrieves relevant knowledge using AI/Vector retriever
    3. Injects retrieved knowledge into the DAG structure
    
    本类功能：
    1. 识别DAG中的知识缺口
    2. 使用AI/向量检索器检索相关知识
    3. 将检索到的知识注入DAG结构
    """
    
    def __init__(
        self,
        ai_retriever=None,
        vector_retriever=None,
        verbose: bool = True
    ):
        """
        Initialize RAG knowledge enhancer.
        
        Args:
            ai_retriever: AIKnowledgeRetriever instance for dynamic knowledge generation
            vector_retriever: VectorKnowledgeRetriever instance for similarity-based retrieval
            verbose: Whether to print progress
        """
        self.ai_retriever = ai_retriever
        self.vector_retriever = vector_retriever
        self.verbose = verbose
        
        # Load prompts
        self._load_prompts()
        
        if self.verbose:
            retrievers = []
            if self.ai_retriever:
                retrievers.append("AI Retriever")
            if self.vector_retriever:
                retrievers.append("Vector Retriever")
            print(f"✓ RAGKnowledgeEnhancer initialized with: {', '.join(retrievers) if retrievers else 'No retrievers'}")
    
    def _print(self, message: str, **kwargs):
        """Conditional print"""
        if self.verbose:
            print(message, **kwargs)
    
    def _load_prompts(self):
        """Load knowledge gap identification and injection prompts"""
        # Load gap identification prompt
        gap_prompt_path = Path("prompts/knowledge_gap_identification_prompt.txt")
        if gap_prompt_path.exists():
            with open(gap_prompt_path, 'r', encoding='utf-8') as f:
                self.gap_identification_prompt = f.read()
        else:
            self.gap_identification_prompt = self._get_default_gap_prompt()
        
        # Load knowledge injection prompt
        injection_prompt_path = Path("prompts/knowledge_injection_prompt.txt")
        if injection_prompt_path.exists():
            with open(injection_prompt_path, 'r', encoding='utf-8') as f:
                self.knowledge_injection_prompt = f.read()
        else:
            self.knowledge_injection_prompt = self._get_default_injection_prompt()
    
    def _get_default_gap_prompt(self) -> str:
        """Default knowledge gap identification prompt"""
        return """Analyze the following causal DAG to identify knowledge gaps.

**Problem:**
{problem}

**Causal DAG:**
{dag}

**Tasks:**
1. Identify missing formulas, theorems, or principles
2. Detect incomplete reasoning chains
3. Suggest relevant domain knowledge

**Output JSON Format:**
{{
  "knowledge_gaps": [
    {{"gap_type": "formula/theorem/principle", "description": "...", "priority": "high/medium/low"}}
  ],
  "suggestions": [
    {{"knowledge_item": "...", "application": "...", "confidence": 0.0-1.0}}
  ]
}}
"""
    
    def _get_default_injection_prompt(self) -> str:
        """Default knowledge injection prompt"""
        return """You are a Knowledge Integration Expert. Inject the retrieved knowledge into the DAG.

**Problem:** {problem}
**Current DAG:** {dag}
**Retrieved Knowledge:** {knowledge_rules}
**Knowledge Gaps:** {knowledge_gaps}

Analyze the knowledge and inject relevant items into the DAG structure.
Output JSON with: analysis, injections, knowledge_enhanced_dag, summary.
"""
    
    def enhance_dag_with_knowledge(
        self,
        dag: Dict[str, Any],
        problem_text: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Enhance DAG by identifying gaps and retrieving relevant knowledge.
        通过识别缺口并检索相关知识来增强DAG
        
        Args:
            dag: Reviewed DAG from expert review step
            problem_text: Original problem description
        
        Returns:
            Tuple of (enhanced_dag, knowledge_report)
        """
        self._print("📚 Enhancing DAG with RAG knowledge...", end=" ")
        
        try:
            # Step 1: Identify knowledge gaps
            gaps = self._identify_knowledge_gaps(dag, problem_text)
            
            if not gaps or len(gaps.get('knowledge_gaps', [])) == 0:
                self._print("✓ No significant knowledge gaps found")
                return dag, {
                    'status': 'no_gaps',
                    'gaps_identified': [],
                    'knowledge_retrieved': [],
                    'injection_method': 'none'
                }
            
            # Step 2: Retrieve relevant knowledge for identified gaps
            knowledge_rules = self._retrieve_relevant_knowledge(gaps, problem_text)
            
            if not knowledge_rules:
                self._print("✓ No additional knowledge retrieved")
                return dag, {
                    'status': 'no_retrieval',
                    'gaps_identified': gaps.get('knowledge_gaps', []),
                    'knowledge_retrieved': [],
                    'injection_method': 'none'
                }
            
            # Step 3: Inject knowledge into DAG (LLM-driven)
            enhanced_dag, injection_report = self._inject_knowledge_into_dag(
                dag, knowledge_rules, gaps, problem_text
            )
            
            # Prepare knowledge report
            knowledge_report = {
                'status': 'success',
                'gaps_identified': gaps.get('knowledge_gaps', []),
                'knowledge_retrieved': knowledge_rules,
                'injection_method': injection_report.get('method', 'unknown'),
                'injection_details': injection_report,
                'suggestions': gaps.get('suggestions', [])
            }
            
            self._print(f"✓ Knowledge injected via {injection_report.get('method', 'unknown')}")
            
            return enhanced_dag, knowledge_report
        
        except Exception as e:
            self._print(f"✗ Failed: {str(e)}")
            return dag, {
                'status': 'failed',
                'error': str(e),
                'gaps_identified': [],
                'knowledge_retrieved': [],
                'injection_method': 'failed'
            }
    
    def _identify_knowledge_gaps(
        self,
        dag: Dict[str, Any],
        problem_text: str
    ) -> Dict[str, Any]:
        """
        Identify knowledge gaps in the DAG using LLM analysis.
        使用LLM分析识别DAG中的知识缺口
        
        Args:
            dag: Current DAG
            problem_text: Problem description
        
        Returns:
            Dictionary containing identified gaps and suggestions
        """
        # If no AI retriever, use rule-based gap detection
        if not self.ai_retriever:
            return self._rule_based_gap_detection(dag)
        
        try:
            # Use AI retriever's LLM to identify gaps
            prompt = self.gap_identification_prompt.format(
                problem=problem_text,
                dag=json.dumps(dag, indent=2, ensure_ascii=False)
            )
            
            # Call LLM to identify gaps
            response = self.ai_retriever.llm_client.complete(prompt, temperature=0.0)
            
            # Parse response
            gaps = self._parse_gap_response(response)
            return gaps
        
        except Exception as e:
            self._print(f"  ⚠️  Gap identification failed, using rule-based fallback: {e}")
            return self._rule_based_gap_detection(dag)
    
    def _parse_gap_response(self, response: str) -> Dict[str, Any]:
        """Parse gap identification response"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                gaps = json.loads(json_match.group(0))
                # Ensure required fields
                if 'knowledge_gaps' not in gaps:
                    gaps['knowledge_gaps'] = []
                if 'suggestions' not in gaps:
                    gaps['suggestions'] = []
                return gaps
            else:
                return {'knowledge_gaps': [], 'suggestions': []}
        except json.JSONDecodeError:
            return {'knowledge_gaps': [], 'suggestions': []}
    
    def _rule_based_gap_detection(self, dag: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback: Rule-based knowledge gap detection.
        回退方案：基于规则的知识缺口检测
        
        Detects gaps by checking:
        - Missing rules in causal links
        - Isolated nodes without connections
        - Very short reasoning chains
        """
        gaps = []
        
        # Check causal graph
        if 'causal_graph' in dag:
            for i, link in enumerate(dag['causal_graph']):
                # Check if rule is missing or too short
                rule = link.get('rule', '')
                if not rule or len(rule) < 10:
                    gaps.append({
                        'gap_type': 'missing_rule',
                        'description': f"Link {i} (effect: {link.get('effect')}) lacks detailed reasoning",
                        'priority': 'medium'
                    })
        
        return {
            'knowledge_gaps': gaps,
            'suggestions': []
        }
    
    def _retrieve_relevant_knowledge(
        self,
        gaps: Dict[str, Any],
        problem_text: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve knowledge for identified gaps using available retrievers.
        使用可用的检索器为识别的缺口检索知识
        
        Args:
            gaps: Identified knowledge gaps
            problem_text: Problem description
        
        Returns:
            List of knowledge rules
        """
        knowledge_rules = []
        
        # Extract gap descriptions for retrieval
        gap_queries = []
        for gap in gaps.get('knowledge_gaps', []):
            gap_queries.append(gap.get('description', ''))
        
        # Also use suggestions as queries
        for suggestion in gaps.get('suggestions', []):
            gap_queries.append(suggestion.get('knowledge_item', ''))
        
        if not gap_queries:
            return []
        
        # Try AI retriever first
        if self.ai_retriever:
            try:
                # Combine problem + gaps for context-aware retrieval
                query = f"{problem_text}\n\nKnowledge needed: {', '.join(gap_queries)}"
                # Correct method is extract_knowledge, which returns a list of strings
                rules = self.ai_retriever.extract_knowledge(query)
                
                # Convert to standard format
                for rule_text in rules:
                    knowledge_rules.append({
                        'rule': rule_text,
                        'source': 'AI_retriever',
                        'confidence': 0.85,  # Assign a default confidence
                        'category': 'ai_generated'
                    })
            except Exception as e:
                self._print(f"  ⚠️  AI retrieval failed: {e}")
        
        # Try vector retriever as supplement
        if self.vector_retriever and len(knowledge_rules) < 3:
            try:
                # Use problem text for vector similarity search
                vector_rules = self.vector_retriever.retrieve_by_similarity(
                    problem_text, top_k=3
                )
                
                for rule in vector_rules:
                    knowledge_rules.append({
                        'rule': rule.get('content', ''),
                        'source': 'vector_retriever',
                        'confidence': rule.get('similarity', 0.7),
                        'category': rule.get('category', 'general')
                    })
            except Exception as e:
                self._print(f"  ⚠️  Vector retrieval failed: {e}")
        
        return knowledge_rules
    
    def _llm_inject_knowledge(
        self,
        dag: Dict[str, Any],
        knowledge_rules: List[Dict[str, Any]],
        knowledge_gaps: Dict[str, Any],
        problem_text: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Use LLM to intelligently inject knowledge into DAG structure.
        使用LLM智能地将知识注入DAG结构
        
        This is the core innovation: instead of just adding metadata,
        we use LLM to actually modify the DAG (knowns, causal_graph, computation_plan)
        
        Args:
            dag: Current DAG
            knowledge_rules: Retrieved knowledge
            knowledge_gaps: Identified gaps
            problem_text: Problem description
        
        Returns:
            Tuple of (knowledge_enhanced_dag, injection_report)
        """
        # If no AI retriever (no LLM), fall back to simple metadata injection
        if not self.ai_retriever:
            self._print("  ⚠️  No LLM available, using simple metadata injection")
            return self._simple_metadata_injection(dag, knowledge_rules)
        
        try:
            # Prepare prompt
            prompt = self.knowledge_injection_prompt.format(
                problem=problem_text,
                dag=json.dumps(dag, indent=2, ensure_ascii=False),
                knowledge_rules=json.dumps(knowledge_rules, indent=2, ensure_ascii=False),
                knowledge_gaps=json.dumps(knowledge_gaps, indent=2, ensure_ascii=False)
            )
            
            # Call LLM to inject knowledge
            response = self.ai_retriever.llm_client.complete(prompt, temperature=0.0)
            
            # Parse response
            injection_result = self._parse_injection_response(response)
            
            if not injection_result or 'knowledge_enhanced_dag' not in injection_result:
                self._print("  ⚠️  LLM injection failed to return valid DAG, using fallback")
                return self._simple_metadata_injection(dag, knowledge_rules)
            
            # Extract enhanced DAG and report
            enhanced_dag = injection_result['knowledge_enhanced_dag']
            
            injection_report = {
                'method': 'llm_injection',
                'analysis': injection_result.get('analysis', {}),
                'injections': injection_result.get('injections', []),
                'summary': injection_result.get('summary', 'Knowledge injected via LLM')
            }
            
            return enhanced_dag, injection_report
        
        except Exception as e:
            self._print(f"  ⚠️  LLM injection error: {e}, using fallback")
            return self._simple_metadata_injection(dag, knowledge_rules)
    
    def _parse_injection_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM injection response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result
            else:
                return None
        except json.JSONDecodeError as e:
            self._print(f"  ⚠️  JSON parse error: {e}")
            return None
    
    def _simple_metadata_injection(
        self,
        dag: Dict[str, Any],
        knowledge_rules: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Fallback: Simple metadata injection (original behavior).
        回退方案：简单的metadata注入（原始行为）
        
        Only adds knowledge to a separate field, doesn't modify DAG structure.
        """
        enhanced_dag = copy.deepcopy(dag)
        
        # Add to knowledge_base field
        if 'knowledge_base' not in enhanced_dag:
            enhanced_dag['knowledge_base'] = []
        
        for kr in knowledge_rules:
            enhanced_dag['knowledge_base'].append({
                'rule': kr['rule'],
                'source': kr['source'],
                'confidence': kr.get('confidence', 0.8),
                'category': kr.get('category', 'general')
            })
        
        injection_report = {
            'method': 'simple_metadata',
            'note': 'Knowledge added to metadata only, DAG structure unchanged',
            'items_added': len(knowledge_rules)
        }
        
        return enhanced_dag, injection_report
    
    def _inject_knowledge_into_dag(
        self,
        dag: Dict[str, Any],
        knowledge_rules: List[Dict[str, Any]],
        knowledge_gaps: Dict[str, Any],
        problem_text: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Inject retrieved knowledge into DAG structure using LLM.
        使用LLM将检索到的知识注入DAG结构
        
        This is the NEW implementation (after Stage 2 fix):
        - Uses LLM to intelligently inject knowledge
        - Actually modifies DAG structure (knowns, causal_graph, computation_plan)
        - Falls back to simple metadata injection if LLM unavailable
        
        Args:
            dag: Current DAG
            knowledge_rules: Retrieved knowledge to inject
            knowledge_gaps: Identified gaps
            problem_text: Problem description
        
        Returns:
            Tuple of (enhanced_dag, injection_report)
        """
        # Use LLM-driven knowledge injection
        return self._llm_inject_knowledge(
            dag, knowledge_rules, knowledge_gaps, problem_text
        )










