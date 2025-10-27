"""
AI-based Knowledge Retriever Module
基于AI的知识检索模块

This module uses Large Language Models to dynamically generate relevant
formulas, principles, and domain knowledge based on problem context,
replacing traditional database retrieval.

本模块使用大语言模型根据问题上下文动态生成相关的公式、原理和领域知识，
取代传统的数据库检索方式。
"""

import json
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class RuleFormat(Enum):
    """
    Output format for generated rules.
    生成规则的输出格式
    """
    SIMPLE_LIST = "simple_list"  # Plain text list / 纯文本列表
    STRUCTURED_JSON = "structured_json"  # JSON with metadata / 带元数据的JSON


@dataclass
class KnowledgeRule:
    """
    Structured representation of a knowledge rule.
    知识规则的结构化表示

    Attributes:
        rule: The formula or principle description
              公式或原理的描述
        category: Domain category (e.g., 'mechanics', 'mathematics')
                  领域分类（例如：'mechanics'力学, 'mathematics'数学）
        confidence: Confidence score (0.0-1.0) if available
                    置信度分数（0.0-1.0），如果可用
        explanation: Additional context or usage notes
                     额外的上下文或使用说明
    """
    rule: str
    category: Optional[str] = None
    confidence: Optional[float] = None
    explanation: Optional[str] = None


class AIKnowledgeRetriever:
    """
    AI-powered Knowledge Retriever for dynamic rule generation.
    基于AI的动态规则生成知识检索器

    This class uses an LLM to analyze problem statements and generate
    contextually relevant formulas, laws, and principles on-the-fly,
    providing more flexibility than static knowledge bases.

    此类使用LLM分析问题陈述，并即时生成上下文相关的公式、定律和原理，
    提供比静态知识库更大的灵活性。

    Key Features / 关键特性:
    - Dynamic rule generation / 动态规则生成
    - Context-aware knowledge extraction / 上下文感知的知识提取
    - Customizable prompts / 可自定义提示词
    - Multiple output formats / 多种输出格式
    - Fallback strategies / 降级策略
    """

    def __init__(
        self,
        llm_client: Optional['LLMClient'] = None,
        prompt_template_path: Optional[str] = "prompts/knowledge_extraction_prompt.txt",
        fallback_retriever: Optional['KnowledgeRetriever'] = None,
        knowledge_base_path: Optional[str] = "data/knowledge_base.json",
        auto_enrich_kb: bool = False,
        max_rules: int = 5,
        temperature: float = 0.3,
        output_format: RuleFormat = RuleFormat.SIMPLE_LIST,
        enable_cache: bool = False,
        verbose: bool = True
    ):
        """
        Initialize the AI knowledge retriever.
        初始化AI知识检索器

        Args:
            llm_client: LLM client instance (creates default if None)
                        LLM客户端实例（如果为None则创建默认实例）
            prompt_template_path: Path to prompt template file or None for default
                                  提示词模板文件路径，None表示使用默认模板
            fallback_retriever: Traditional retriever to use if AI fails
                                AI失败时使用的传统检索器
            knowledge_base_path: Path to knowledge base JSON file for saving rules
                                 用于保存规则的知识库JSON文件路径
            auto_enrich_kb: Whether to automatically add generated rules to knowledge base
                            是否自动将生成的规则添加到知识库
            max_rules: Maximum number of rules to generate
                       生成规则的最大数量
            temperature: LLM sampling temperature (0.0-1.0)
                         LLM采样温度（0.0-1.0）
            output_format: Format for rule output
                           规则输出格式
            enable_cache: Whether to cache generated rules
                          是否缓存生成的规则
            verbose: Whether to print detailed progress
                     是否打印详细进度
        """
        # Lazy import to avoid circular dependency
        # 延迟导入以避免循环依赖
        from engine.scaffolder import LLMClient

        self.llm_client = llm_client or LLMClient()
        self.fallback_retriever = fallback_retriever
        self.knowledge_base_path = Path(knowledge_base_path) if knowledge_base_path else None
        self.auto_enrich_kb = auto_enrich_kb
        self.max_rules = max_rules
        self.temperature = temperature
        self.output_format = output_format
        self.enable_cache = enable_cache
        self.verbose = verbose

        # Load prompt template / 加载提示词模板
        self.prompt_template = self._load_prompt_template(prompt_template_path)

        # Initialize cache / 初始化缓存
        self.cache: Dict[str, List[str]] = {} if enable_cache else None

        # Track problem-rule mappings for KB enrichment
        # 跟踪问题-规则映射以便丰富知识库
        self.problem_rule_history: List[Dict[str, Any]] = []
        
        # Store structured rules from last extraction (for KB enrichment)
        # 存储上次提取的结构化规则（用于知识库丰富）
        self.last_structured_rules: List[Dict[str, Any]] = []
        
        # Semantic embedding for duplicate detection (lazy loading)
        # 用于重复检测的语义嵌入（懒加载）
        self._embedding_model = None
        self._embeddings_cache: Dict[str, Any] = {}  # Cache embeddings
        self.use_semantic_dedup = True  # Enable semantic deduplication by default

        self._print("Initialized AI Knowledge Retriever.")
        self._print("已初始化AI知识检索器")

        if auto_enrich_kb:
            self._print("   Auto-enrichment of knowledge base is ENABLED.")
            self._print("   知识库自动丰富功能已启用")

    def _print(self, message: str) -> None:
        """
        Print message if verbose mode is enabled.
        如果启用详细模式，则打印消息

        Args:
            message: Message to print
                     要打印的消息
        """
        if self.verbose:
            print(message)

    def _load_prompt_template(self, template_path: Optional[str]) -> str:
        """
        Load prompt template from file or use default.
        从文件加载提示词模板或使用默认模板

        Args:
            template_path: Path to template file or None
                           模板文件路径，None表示使用默认

        Returns:
            Prompt template string
            提示词模板字符串
        """
        if template_path:
            path = Path(template_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self._print(f"Loaded custom prompt template from: {path}")
                    self._print(f"已从以下位置加载自定义提示词模板: {path}")
                    return f.read()
            else:
                self._print(f"Warning: Template file not found: {path}, using default.")
                self._print(f"警告: 未找到模板文件: {path}，使用默认模板")

        return self._get_default_prompt_template()

    def _get_default_prompt_template(self) -> str:
        """
        Get the default prompt template for knowledge extraction.
        获取知识提取的默认提示词模板

        Returns:
            Default prompt template
            默认提示词模板
        """
        return """**ROLE:**
You are an expert in mathematics, physics, and scientific reasoning. Your task is to identify and articulate all relevant formulas, laws, principles, and rules needed to solve a given problem.

**OBJECTIVE:**
Analyze the problem statement and generate a comprehensive list of domain knowledge required for solving it. Focus on being precise, relevant, and complete.

**INSTRUCTIONS:**
1. Carefully read and understand the problem domain (e.g., mechanics, thermodynamics, geometry, algebra).
2. Identify all physical laws, mathematical formulas, and principles applicable to this problem.
3. For each rule, provide:
   - A clear name or description
   - The mathematical formula or expression
   - Brief context on when and how to apply it
4. List up to {max_rules} most relevant rules.
5. Order rules by relevance (most important first).

**OUTPUT FORMAT:**
Provide a numbered list where each entry follows this structure:
```
N. [Name/Description]: [Formula/Expression] - [Brief explanation of application]
```

**EXAMPLE:**
Problem: "An object with mass 10 kg starts from rest. A force of 50 N acts on it for 5 seconds. Find the final velocity."

Output:
1. Newton's Second Law: F = m × a - Relates force, mass, and acceleration. Use to find acceleration when force and mass are known.
2. Kinematic Equation (Constant Acceleration): v_f = v_i + a × t - Calculates final velocity given initial velocity, acceleration, and time.
3. Rest Condition: v_i = 0 - When an object is at rest, its initial velocity is zero.

**YOUR TASK:**
Analyze the following problem and generate the required knowledge rules:

**PROBLEM:**
{problem_text}

**OUTPUT:**
"""

    def get_knowledge(self, problem_text: str) -> List[str]:
        """
        Main interface for knowledge extraction (compatible with KnowledgeRetriever).
        知识提取的主接口（与KnowledgeRetriever兼容）

        This method provides the same interface as the traditional KnowledgeRetriever,
        making it a drop-in replacement.

        此方法提供与传统KnowledgeRetriever相同的接口，使其可以直接替换使用。

        Args:
            problem_text: The problem statement in natural language
                          自然语言的问题陈述

        Returns:
            List of relevant rule descriptions
            相关规则描述的列表
        """
        return self.extract_knowledge(problem_text)

    def extract_knowledge(
        self,
        problem_text: str,
        use_fallback_on_error: bool = True
    ) -> List[str]:
        """
        Extract relevant knowledge rules using AI generation.
        使用AI生成方式提取相关的知识规则

        This method sends the problem to the LLM and parses the generated
        formulas, laws, and principles.

        此方法将问题发送给LLM，并解析生成的公式、定律和原理。

        Args:
            problem_text: The problem statement
                          问题陈述
            use_fallback_on_error: Whether to use fallback retriever on error
                                   错误时是否使用降级检索器

        Returns:
            List of relevant rule descriptions
            相关规则描述的列表
        """
        # Check cache first / 首先检查缓存
        if self.enable_cache and problem_text in self.cache:
            self._print("Retrieved rules from cache.")
            self._print("从缓存中检索到规则")
            return self.cache[problem_text]

        self._print("\n" + "="*60)
        self._print("Extracting knowledge using AI...")
        self._print("使用AI提取知识...")
        self._print("="*60)

        try:
            # Generate prompt / 生成提示词
            prompt = self.prompt_template.format(
                problem_text=problem_text,
                max_rules=self.max_rules
            )

            # Call LLM / 调用LLM
            self._print("Calling LLM for knowledge generation...")
            self._print("正在调用LLM生成知识...")

            response = self.llm_client.complete(prompt, temperature=self.temperature)

            # Parse response / 解析响应
            rules = self._parse_rules(response)

            # Validate rules / 验证规则
            if not rules:
                self._print("Warning: No rules were extracted from LLM response.")
                self._print("警告: 未从LLM响应中提取到规则")
                if use_fallback_on_error and self.fallback_retriever:
                    return self._use_fallback(problem_text)
                return []

            # Cache results / 缓存结果
            if self.enable_cache:
                self.cache[problem_text] = rules

            # Auto-enrich knowledge base if enabled
            # 如果启用，自动丰富知识库
            if self.auto_enrich_kb and rules:
                self._save_rules_to_kb(problem_text, rules)

            self._print(f"\n Successfully extracted {len(rules)} relevant rules.")
            self._print(f" 成功提取了 {len(rules)} 条相关规则")
            self._print("="*60 + "\n")

            return rules

        except Exception as e:
            self._print(f"\n Error during AI knowledge extraction: {e}")
            self._print(f" AI知识提取过程中出错: {e}")

            if use_fallback_on_error and self.fallback_retriever:
                return self._use_fallback(problem_text)

            self._print("No fallback retriever available, returning empty list.")
            self._print("没有可用的降级检索器，返回空列表")
            return []

    def _parse_rules(self, response: str) -> List[str]:
        """
        Parse the LLM response to extract individual rules.
        解析LLM响应以提取单个规则

        This method handles various output formats and extracts clean,
        usable rule descriptions. Now supports JSON format output.

        此方法处理各种输出格式并提取清晰、可用的规则描述。现在支持JSON格式输出。

        Args:
            response: The raw LLM response text
                      LLM原始响应文本

        Returns:
            List of extracted rules
            提取的规则列表
        """
        rules = []
        
        # Clear previous structured rules
        # 清除之前的结构化规则
        self.last_structured_rules = []

        # Strategy 1: Parse JSON format (NEW - for updated prompt template)
        # 策略1: 解析JSON格式（新增 - 适配更新的prompt模板）
        try:
            # Extract JSON content from response
            # 从响应中提取JSON内容
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON array without code blocks
                # 尝试查找没有代码块的JSON数组
                json_match = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = None

            if json_str:
                # Parse JSON
                # 解析JSON
                json_data = json.loads(json_str)
                
                if isinstance(json_data, list):
                    for item in json_data[:self.max_rules]:
                        if isinstance(item, dict):
                            # Extract rule from JSON object
                            # 从JSON对象中提取规则
                            rule_text = item.get('rule', '')
                            
                            # Extract keywords and category from LLM response
                            # 从LLM响应中提取关键词和分类
                            keywords = item.get('keywords', [])
                            category = item.get('category', '')
                            
                            if rule_text and len(rule_text) > 15:
                                # Store structured data for KB enrichment
                                # 存储结构化数据用于知识库丰富
                                self.last_structured_rules.append({
                                    'keywords': keywords,
                                    'rule': rule_text,
                                    'category': category
                                })
                                
                                # Format: rule text (with optional metadata)
                                # 格式：规则文本（带可选元数据）
                                formatted_rule = rule_text
                                
                                # Add category if available
                                # 如果有分类则添加
                                if category:
                                    formatted_rule = f"[{category}] {formatted_rule}"
                                
                                rules.append(formatted_rule)
                
                # If we successfully parsed JSON rules, return them
                # 如果成功解析了JSON规则，返回它们
                if rules:
                    self._print(f"  ✓ Successfully parsed {len(rules)} rules from JSON format")
                    self._print(f"  ✓ 成功从JSON格式解析了 {len(rules)} 条规则")
                    self._print(f"  ✓ Stored {len(self.last_structured_rules)} structured rules for KB enrichment")
                    self._print(f"  ✓ 已存储 {len(self.last_structured_rules)} 条结构化规则用于知识库丰富")
                    return rules
        
        except json.JSONDecodeError as e:
            self._print(f"  ⚠ JSON parsing failed: {e}, trying fallback methods")
            self._print(f"  ⚠ JSON解析失败: {e}，尝试fallback方法")
        except Exception as e:
            self._print(f"  ⚠ Error parsing JSON: {e}, trying fallback methods")
            self._print(f"  ⚠ 解析JSON时出错: {e}，尝试fallback方法")

        # Strategy 2: Parse numbered list (e.g., "1.", "2.", etc.) - FALLBACK
        # 策略2: 解析编号列表（例如"1.","2."等）- 备用方案
        # Match patterns like: "1. Name: Formula - Explanation"
        pattern = r'\d+\.\s+(.+?)(?=\n\d+\.|\n*$)'
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            for match in matches:
                rule = match.strip()
                if rule and len(rule) > 15:  # Filter out very short matches
                    rules.append(rule)

            # Limit to max_rules
            if rules:
                self._print(f"  ✓ Parsed {len(rules)} rules from numbered list format")
                self._print(f"  ✓ 从编号列表格式解析了 {len(rules)} 条规则")
                return rules[:self.max_rules]

        # Strategy 3: Split by newlines and clean up - LAST RESORT
        # 策略3: 按换行符分割并清理 - 最后的手段
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()

            # Remove leading numbers and common list markers
            # 删除前导数字和常见列表标记
            cleaned = re.sub(r'^[\d\-\*\]+[\.\)]\s*', '', line)

            # Filter: must be substantial and likely a rule description
            # 过滤：必须是实质性的并且可能是规则描述
            if cleaned and len(cleaned) > 15 and ':' in cleaned:
                rules.append(cleaned)

                if len(rules) >= self.max_rules:
                    break

        if rules:
            self._print(f"  ✓ Parsed {len(rules)} rules from line-by-line format")
            self._print(f"  ✓ 从逐行格式解析了 {len(rules)} 条规则")
        
        return rules

    def _use_fallback(self, problem_text: str) -> List[str]:
        """
        Use fallback retriever when AI extraction fails.
         AI 

        Args:
            problem_text: The problem statement
                          

        Returns:
            Rules from fallback retriever
            
        """
        self._print("\n Using fallback retriever (traditional knowledge base)...")
        self._print(" ...")

        try:
            rules = self.fallback_retriever.get_knowledge(problem_text)
            self._print(f"  Fallback retriever returned {len(rules)} rules.")
            self._print(f"   {len(rules)} ")
            return rules
        except Exception as e:
            self._print(f"  Fallback retriever also failed: {e}")
            self._print(f"  : {e}")
            return []

    def extract_structured_knowledge(
        self,
        problem_text: str
    ) -> List[KnowledgeRule]:
        """
        Extract knowledge in structured format with metadata.
        

        This method returns KnowledgeRule objects instead of plain strings,
        providing additional metadata for advanced use cases.

         KnowledgeRule 
        

        Args:
            problem_text: The problem statement
                          

        Returns:
            List of structured KnowledgeRule objects
             KnowledgeRule 
        """
        # Get raw rules / 
        raw_rules = self.extract_knowledge(problem_text)

        # Convert to structured format / 
        structured_rules = []
        for rule_text in raw_rules:
            # Try to parse structured information from rule text
            # 
            structured_rule = self._parse_structured_rule(rule_text)
            structured_rules.append(structured_rule)

        return structured_rules

    def _parse_structured_rule(self, rule_text: str) -> KnowledgeRule:
        """
        Parse a rule string into a structured KnowledgeRule object.
         KnowledgeRule 

        Args:
            rule_text: Raw rule text
                       

        Returns:
            KnowledgeRule object
            KnowledgeRule 
        """
        # Basic implementation: just wrap the text
        # 
        # TODO: Enhanced parsing to extract category, formula, etc.
        # TODO
        return KnowledgeRule(
            rule=rule_text,
            category=None,
            confidence=None,
            explanation=None
        )

    def clear_cache(self) -> None:
        """
        Clear the cached rules.
        
        """
        if self.cache is not None:
            self.cache.clear()
            self._print("Cache cleared.")
            self._print("")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        

        Returns:
            Dictionary with cache statistics
            
        """
        if not self.enable_cache:
            return {"enabled": False}

        return {
            "enabled": True,
            "size": len(self.cache),
            "problems_cached": list(self.cache.keys())
        }

    def _save_rules_to_kb(self, problem_text: str, rules: List[str]) -> None:
        """
        Save generated rules to the knowledge base.
        将生成的规则保存到知识库
        
        This method uses the structured data from LLM (keywords, rule, category)
        stored in self.last_structured_rules to save to knowledge base.
        If structured data is not available, falls back to extracting keywords
        from the problem text.
        
        此方法使用存储在 self.last_structured_rules 中的LLM结构化数据
        （关键词、规则、分类）保存到知识库。如果没有结构化数据，
        则降级为从问题文本中提取关键词。

        Args:
            problem_text: The problem statement
                          问题陈述
            rules: List of generated rules (for compatibility)
                   生成的规则列表（用于兼容性）
        """
        if not self.knowledge_base_path:
            self._print("   Knowledge base path not set, skipping save.")
            self._print("   ")
            return

        try:
            # Load existing knowledge base
            # 加载现有知识库
            kb_data = self._load_knowledge_base()

            # Use structured rules if available (from JSON parsing)
            # 如果有结构化规则（来自JSON解析），则使用它们
            if self.last_structured_rules:
                new_entries_count = 0
                
                for structured_rule in self.last_structured_rules:
                    rule_text = structured_rule.get('rule', '')
                    keywords = structured_rule.get('keywords', [])
                    category = structured_rule.get('category', 'ai_generated')
                    
                    # Check if rule already exists (avoid duplicates)
                    # 检查规则是否已存在（避免重复）
                    if not self._rule_exists_in_kb(rule_text, kb_data):
                        kb_entry = {
                            "keywords": keywords if keywords else ["general"],
                            "rule": rule_text,
                            "category": category,
                            "source": "ai_retriever"
                        }
                        kb_data.append(kb_entry)
                        new_entries_count += 1
                        
                        # Print the rule being added to KB
                        # 打印正在添加到知识库的规则
                        self._print(f"   📝 Adding to KB → [{category}] {rule_text}")
                        self._print(f"   📝 添加到知识库 → [关键词: {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}]")

                        # Track in history
                        # 记录到历史
                        self.problem_rule_history.append({
                            "problem": problem_text[:100] + "..." if len(problem_text) > 100 else problem_text,
                            "rule": rule_text,
                            "keywords": keywords,
                            "category": category
                        })
                
                # Save updated knowledge base
                # 保存更新的知识库
                if new_entries_count > 0:
                    self._write_knowledge_base(kb_data)
                    self._print(f"   ✓ Added {new_entries_count} new structured rules to knowledge base.")
                    self._print(f"   ✓ 向知识库添加了 {new_entries_count} 条新的结构化规则")
                else:
                    self._print("   ℹ All rules already exist in knowledge base.")
                    self._print("   ℹ 所有规则已存在于知识库中")
            
            else:
                # Fallback: Extract keywords from problem (for non-JSON formats)
                # 后备方案：从问题中提取关键词（用于非JSON格式）
                self._print("   ⚠ No structured rules available, using fallback method")
                self._print("   ⚠ 没有可用的结构化规则，使用后备方法")
                
                keywords = self._extract_keywords_from_problem(problem_text)
                new_entries_count = 0
                
                for rule in rules:
                    if not self._rule_exists_in_kb(rule, kb_data):
                        # Remove category prefix if exists (e.g., "[algebra] ...")
                        # 如果存在分类前缀则删除（例如："[algebra] ..."）
                        clean_rule = re.sub(r'^\[[\w\s]+\]\s*', '', rule)
                        
                        kb_entry = {
                            "keywords": keywords,
                            "rule": clean_rule,
                            "category": "ai_generated",
                            "source": "ai_retriever"
                        }
                        kb_data.append(kb_entry)
                        new_entries_count += 1
                        
                        # Print the rule being added to KB
                        # 打印正在添加到知识库的规则
                        self._print(f"   📝 Adding to KB → [ai_generated] {clean_rule}")
                        self._print(f"   📝 添加到知识库 → [关键词: {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}]")

                        self.problem_rule_history.append({
                            "problem": problem_text[:100] + "..." if len(problem_text) > 100 else problem_text,
                            "rule": clean_rule,
                            "keywords": keywords
                        })

                if new_entries_count > 0:
                    self._write_knowledge_base(kb_data)
                    self._print(f"   Added {new_entries_count} new rules to knowledge base.")
                    self._print(f"   向知识库添加了 {new_entries_count} 条新规则")
                else:
                    self._print("   All rules already exist in knowledge base.")
                    self._print("   所有规则已存在于知识库中")

        except Exception as e:
            self._print(f"   ❌ Error saving rules to KB: {e}")
            self._print(f"   ❌ 保存规则到知识库时出错: {e}")
            import traceback
            if self.verbose:
                traceback.print_exc()

    def _extract_keywords_from_problem(self, problem_text: str) -> List[str]:
        """
        Extract keywords from problem text for knowledge base indexing.
        

        This method uses a comprehensive domain-specific keyword database
        to identify relevant academic terms in the problem.

        

        Args:
            problem_text: The problem statement
                          

        Returns:
            List of extracted keywords
            
        """
        # Use the comprehensive domain keywords database
        # 
        from .domain_keywords import extract_keywords_from_text, identify_domains

        # Extract keywords using the domain keywords module
        # 
        extracted = extract_keywords_from_text(problem_text, max_keywords=15)

        # If still too few keywords, add domain names
        # 
        if len(extracted) < 3:
            domains = identify_domains(problem_text)
            if domains:
                # Add top 2 domain names
                top_domains = sorted(domains.items(), key=lambda x: x[1]["count"], reverse=True)[:2]
                extracted.extend([domain for domain, _ in top_domains])
            else:
                # Fallback to generic keywords
                extracted.extend(["problem", "solve"])

        return extracted[:15]  # Limit to 15 keywords

    def _load_knowledge_base(self) -> List[Dict[str, Any]]:
        """
        Load the knowledge base from JSON file.
         JSON 

        Returns:
            List of knowledge base entries
            
        """
        if not self.knowledge_base_path.exists():
            self._print(f"   Creating new knowledge base at: {self.knowledge_base_path}")
            self._print(f"   : {self.knowledge_base_path}")
            return []

        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            self._print("   Knowledge base JSON is corrupted, creating new one.")
            self._print("    JSON ")
            return []
        except Exception as e:
            self._print(f"   Error loading KB: {e}")
            self._print(f"   : {e}")
            return []

    def _write_knowledge_base(self, kb_data: List[Dict[str, Any]]) -> None:
        """
        Write knowledge base data to JSON file.
         JSON 

        Args:
            kb_data: Knowledge base entries to write
                     
        """
        # Ensure parent directory exists
        # 
        self.knowledge_base_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.knowledge_base_path, 'w', encoding='utf-8') as f:
            json.dump(kb_data, f, indent=2, ensure_ascii=False)

    def _load_embedding_model(self):
        """
        Lazy load the sentence transformer model for semantic similarity.
        懒加载用于语义相似度的句子转换模型
        
        Returns:
            Loaded model or None if loading fails
            加载的模型，如果加载失败则返回None
        """
        if self._embedding_model is not None:
            return self._embedding_model
        
        try:
            from sentence_transformers import SentenceTransformer
            from pathlib import Path
            
            # Use a lightweight but effective model
            # 使用轻量级但有效的模型
            # Try local path first, then download from hub
            # 首先尝试本地路径，然后从hub下载
            local_model_path = Path('all-MiniLM-L6-v2')
            
            if local_model_path.exists():
                model_name = str(local_model_path)
                self._print(f"   Loading local semantic embedding model: {local_model_path}...")
                self._print(f"   正在加载本地语义嵌入模型: {local_model_path}...")
            else:
                model_name = 'all-MiniLM-L6-v2'  # 80MB, fast, good for short texts
                self._print(f"   Loading semantic embedding model: {model_name}...")
                self._print(f"   正在加载语义嵌入模型: {model_name}...")
            
            self._embedding_model = SentenceTransformer(model_name)
            
            self._print("   ✓ Semantic embedding model loaded successfully.")
            self._print("   ✓ 语义嵌入模型加载成功")
            
            return self._embedding_model
            
        except ImportError:
            self._print("   ⚠ sentence-transformers not installed. Falling back to simple similarity.")
            self._print("   ⚠ 未安装 sentence-transformers。降级使用简单相似度。")
            self._print("   Install with: pip install sentence-transformers")
            self.use_semantic_dedup = False  # Disable semantic dedup
            return None
        except Exception as e:
            self._print(f"   ⚠ Failed to load embedding model: {e}")
            self._print(f"   ⚠ 加载嵌入模型失败: {e}")
            self.use_semantic_dedup = False
            return None
    
    def _get_embedding(self, text: str):
        """
        Get embedding vector for a text.
        获取文本的嵌入向量
        
        Args:
            text: Text to embed
                  要嵌入的文本
        
        Returns:
            Embedding vector or None
            嵌入向量或None
        """
        # Check cache first
        # 首先检查缓存
        if text in self._embeddings_cache:
            return self._embeddings_cache[text]
        
        # Load model if not loaded
        # 如果模型未加载，则加载
        model = self._load_embedding_model()
        if model is None:
            return None
        
        try:
            # Generate embedding
            # 生成嵌入
            embedding = model.encode(text, convert_to_tensor=False)
            
            # Cache it
            # 缓存它
            self._embeddings_cache[text] = embedding
            
            return embedding
        except Exception as e:
            self._print(f"   ⚠ Error generating embedding: {e}")
            return None
    
    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts using embeddings.
        使用嵌入计算两个文本之间的语义相似度
        
        Args:
            text1: First text
                   第一个文本
            text2: Second text
                   第二个文本
        
        Returns:
            Similarity score (0.0-1.0), or -1.0 if calculation fails
            相似度分数（0.0-1.0），如果计算失败则返回-1.0
        """
        if not self.use_semantic_dedup:
            return -1.0
        
        # Get embeddings
        # 获取嵌入
        emb1 = self._get_embedding(text1)
        emb2 = self._get_embedding(text2)
        
        if emb1 is None or emb2 is None:
            return -1.0
        
        try:
            # Calculate cosine similarity
            # 计算余弦相似度
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            # Reshape for sklearn
            # 为sklearn重塑
            emb1 = np.array(emb1).reshape(1, -1)
            emb2 = np.array(emb2).reshape(1, -1)
            
            similarity = cosine_similarity(emb1, emb2)[0][0]
            
            return float(similarity)
            
        except Exception as e:
            self._print(f"   ⚠ Error calculating similarity: {e}")
            return -1.0
    
    def _rule_exists_in_kb(self, rule: str, kb_data: List[Dict[str, Any]]) -> bool:
        """
        Check if a rule already exists in the knowledge base.
        检查规则是否已存在于知识库中
        
        Enhanced with semantic similarity detection:
        增强了语义相似度检测：
        1. Exact match (case-insensitive)
           完全匹配（不区分大小写）
        2. Semantic similarity > 0.85 (if enabled)
           语义相似度 > 0.85（如果启用）
        3. Simple word similarity > 0.9 (fallback)
           简单词相似度 > 0.9（降级）

        Args:
            rule: Rule text to check
                  要检查的规则文本
            kb_data: Knowledge base data
                     知识库数据

        Returns:
            True if rule exists, False otherwise
            如果规则存在则返回True，否则返回False
        """
        rule_lower = rule.lower()
        
        for entry in kb_data:
            existing_rule = entry.get("rule", "")
            existing_lower = existing_rule.lower()
            
            # Check 1: Exact match
            # 检查1：完全匹配
            if rule_lower == existing_lower:
                return True
            
            # Check 2: Semantic similarity (if enabled)
            # 检查2：语义相似度（如果启用）
            if self.use_semantic_dedup:
                semantic_sim = self._semantic_similarity(rule, existing_rule)
                # Use lower threshold (0.60) for formulas vs natural language
                # 对于公式与自然语言使用较低阈值（0.60）
                if semantic_sim > 0.60:  # Adjusted threshold for better detection
                    if self.verbose:
                        self._print(f"   🔍 Semantic duplicate detected (similarity: {semantic_sim:.2f})")
                        self._print(f"   🔍 检测到语义重复（相似度: {semantic_sim:.2f}）")
                    return True
            
            # Check 3: Simple word-based similarity (fallback)
            # 检查3：简单的基于词的相似度（降级）
            if self._similarity(rule_lower, existing_lower) > 0.9:
                return True
        
        return False

    def _similarity(self, s1: str, s2: str) -> float:
        """
        Calculate simple similarity between two strings.
        

        Args:
            s1: First string
                
            s2: Second string
                

        Returns:
            Similarity score (0.0-1.0)
            0.0-1.0
        """
        # Simple word-based similarity
        # 
        words1 = set(s1.split())
        words2 = set(s2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def export_enrichment_history(self, output_path: str = "kb_enrichment_history.json") -> None:
        """
        Export the history of knowledge base enrichment to a file.
        

        Args:
            output_path: Path to save the history
                         
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.problem_rule_history, f, indent=2, ensure_ascii=False)

        self._print(f"Enrichment history exported to: {output_file}")
        self._print(f": {output_file}")

    def get_enrichment_stats(self) -> Dict[str, Any]:
        """
        Get statistics about knowledge base enrichment.
        

        Returns:
            Dictionary with enrichment statistics
            
        """
        return {
            "auto_enrich_enabled": self.auto_enrich_kb,
            "total_rules_generated": len(self.problem_rule_history),
            "knowledge_base_path": str(self.knowledge_base_path) if self.knowledge_base_path else None
        }


# Example usage / 
if __name__ == "__main__":
    from engine.retriever import KnowledgeRetriever

    # Test problem / 
    test_problem = """
    An object with a mass of 10 kg is initially at rest.
    A constant force of 50 Newtons is applied to it for 5 seconds.
    What is its final velocity?
    """

    print("="*70)
    print("Testing AI Knowledge Retriever")
    print(" AI ")
    print("="*70)

    # Initialize with fallback / 
    try:
        fallback = KnowledgeRetriever("data/knowledge_base.json")
    except:
        fallback = None
        print("Note: Traditional retriever not available for fallback.")
        print("")

    retriever = AIKnowledgeRetriever(
        fallback_retriever=fallback,
        max_rules=5,
        enable_cache=True,
        verbose=True
    )

    # Extract knowledge / 
    rules = retriever.get_knowledge(test_problem)

    print("\n" + "="*70)
    print("EXTRACTED RULES")
    print("")
    print("="*70)

    for i, rule in enumerate(rules, 1):
        print(f"\n{i}. {rule}")

    # Test cache / 
    print("\n" + "="*70)
    print("Testing cache...")
    print("...")
    print("="*70)

    rules_cached = retriever.get_knowledge(test_problem)
    print(f"\nCache stats: {retriever.get_cache_stats()}")
    print(f": {retriever.get_cache_stats()}")
