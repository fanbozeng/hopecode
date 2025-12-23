"""
Evaluation Framework / 评估框架

Overview / 概述
- Runs and compares multiple solving methods on several datasets.
  在多个数据集上运行并比较多种求解方法。
- Methods include baselines (Direct LLM, Zero‑shot CoT, Few‑shot CoT),
  the full framework pipeline, and ablations (e.g., no retriever).
  方法包括基线（直接LLM、零样本CoT、少样本CoT）、完整框架管道以及消融实验（如不使用检索器）。
- Outputs per‑problem results, method statistics, and a comparison table.
  输出每个问题的结果、方法统计和对比表。

Key Components / 核心组件
1. DatasetLoader: Load multiple math datasets (GSM8K, MATH, OlympiadBench, etc.)
   数据集加载器：加载多种数学数据集（GSM8K、MATH、OlympiadBench等）
2. BaselineEvaluator: Implement baseline solving methods
   基线评估器：实现基线求解方法
3. FrameworkEvaluator: Evaluate full framework and ablation variants
   框架评估器：评估完整框架和消融变体
4. EvaluationMethod: Enumeration of all supported methods
   评估方法：所有支持方法的枚举
5. EvaluationResult: Structured result for each problem
   评估结果：每个问题的结构化结果
"""

# 标准库导入 / Standard library imports
import json          # JSON 序列化和反序列化 / JSON serialization and deserialization
import sys           # 系统相关功能（退出码等）/ System-specific functions (exit codes, etc.)
import time          # 时间测量（执行时间统计）/ Time measurement (execution time tracking)
import re            # 正则表达式（答案提取和比较）/ Regular expressions (answer extraction and comparison)
from pathlib import Path          # 路径操作 / Path operations
from typing import List, Dict, Any, Optional, Tuple  # 类型注解 / Type annotations
from dataclasses import dataclass, asdict  # 数据类和转换 / Data classes and conversion
from datetime import datetime     # 日期时间（时间戳）/ Date and time (timestamps)
from enum import Enum            # 枚举类型 / Enumeration types

# 导入基线方法模块 / Import baseline method modules
# 这些是用于对比的基线求解方法 / These are baseline solving methods for comparison
from baselines import DirectLLM, ZeroShotCoT, FewShotCoT


class EvaluationMethod(Enum):
    """Enumeration of supported evaluation methods.
    支持的评估方法枚举。

    Baselines / 基线方法
    - DIRECT_LLM: Ask the LLM to answer directly.
      直接LLM：直接让LLM回答问题，无推理过程。
    - ZERO_SHOT_COT: Zero‑shot chain‑of‑thought prompting.
      零样本CoT：零样本思维链提示，让LLM逐步推理。
    - FEW_SHOT_COT: Few‑shot chain‑of‑thought prompting.
      少样本CoT：少样本思维链提示，提供示例引导推理。

    Framework Variants / 框架变体
    - FULL_FRAMEWORK: Full four‑stage pipeline (retrieval → scaffold → compute → synthesize).
      完整框架：四阶段完整流程（检索 → 脚手架 → 计算 → 合成）。

    Ablations / 消融实验
    - NO_RETRIEVER: Disable knowledge retriever.
      无检索器：禁用知识检索器（传统和AI检索器都禁用）。
    - NO_AI_RETRIEVER: Use only traditional retriever (no AI rule generation).
      无AI检索器：仅使用传统检索器（不使用AI生成规则）。
    - NO_SYMBOLIC_EXECUTION: Use LLM computation instead of symbolic execution.
      无符号执行：使用LLM计算而非符号执行。
    - NO_VALIDATION: Skip synthesis/validation.
      无验证：跳过合成/验证阶段。
    """
    # 基线方法 / Baselines
    DIRECT_LLM = "direct_llm"              # 直接LLM / Direct LLM
    ZERO_SHOT_COT = "zero_shot_cot"        # 零样本CoT / Zero-shot CoT
    FEW_SHOT_COT = "few_shot_cot"          # 少样本CoT / Few-shot CoT

    # 我们的框架 / Our Framework
    FULL_FRAMEWORK = "full_framework"      # 完整框架 / Full framework

    # 消融实验 / Ablations
    NO_RETRIEVER = "no_retriever"                      # 无检索器 / No retriever
    NO_AI_RETRIEVER = "no_ai_retriever"                # 无AI检索器 / No AI retriever
    NO_SYMBOLIC_EXECUTION = "no_symbolic_execution"    # 无符号执行 / No symbolic execution
    NO_VALIDATION = "no_validation"                    # 无验证 / No validation


@dataclass
class EvaluationResult:
    """Per‑problem evaluation outcome.
    单个问题的评估结果。

    Fields / 字段
    - problem_id: Unique identifier of the problem.
      问题ID：问题的唯一标识符。
    - method: Evaluation method used (string value of EvaluationMethod).
      方法：使用的评估方法（EvaluationMethod的字符串值）。
    - problem_text: Original problem text.
      问题文本：原始问题文本。
    - expected_answer: Ground‑truth answer from dataset.
      预期答案：数据集中的标准答案。
    - predicted_answer: Model/framework predicted answer (stringified).
      预测答案：模型/框架预测的答案（字符串化）。
    - is_correct: Whether predicted matches expected (via comparator).
      是否正确：预测答案是否与预期答案匹配（通过比较器判断）。
    - execution_time: Wall‑clock time spent to produce prediction.
      执行时间：生成预测所花费的实际时间（秒）。
    - error: Error message if any stage failed.
      错误信息：如果任何阶段失败的错误消息。
    - reasoning_steps: Optional reasoning text for CoT methods.
      推理步骤：CoT方法的推理文本（可选）。
    - causal_scaffold: Optional scaffold for visualization/debugging.
      因果脚手架：用于可视化/调试的脚手架结构（可选）。
    """
    problem_id: str                          # 问题唯一标识符 / Problem unique identifier
    method: str                              # 评估方法名称 / Evaluation method name
    problem_text: str                        # 原始问题文本 / Original problem text
    expected_answer: str                     # 标准答案 / Ground-truth answer
    predicted_answer: Optional[str]          # 预测答案 / Predicted answer
    is_correct: bool                         # 是否正确 / Whether correct
    execution_time: float                    # 执行时间（秒）/ Execution time (seconds)
    error: Optional[str]                     # 错误信息 / Error message
    reasoning_steps: Optional[str] = None    # 推理步骤 / Reasoning steps
    causal_scaffold: Optional[Dict[str, Any]] = None  # 因果脚手架 / Causal scaffold


class DatasetLoader:
    """
    Dataset Loader for multiple formats
    多格式数据集加载器
    
    This class provides static methods to load different math reasoning datasets.
    该类提供静态方法来加载不同的数学推理数据集。
    
    Supported datasets / 支持的数据集：
    - GSM8K: Grade school math problems / 小学数学问题
    - MATH: Competition-level math problems / 竞赛级数学问题
    - MyData: Custom dataset / 自定义数据集
    - Omni-MATH: Comprehensive math reasoning / 综合数学推理
    - OlympiadBench: Olympiad-level problems (multi-modal support) / 奥林匹克级问题（支持多模态）
    """

    @staticmethod
    def load_gsm8k(file_path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load GSM8K dataset / 加载 GSM8K 数据集
        
        GSM8K is a dataset of grade school math problems in JSONL format.
        GSM8K 是小学数学问题数据集，JSONL 格式。
        
        Each line contains:
        每行包含：
        - question: The math problem / 数学问题
        - answer: Solution with final answer after '####' / 解答（'####'后面是最终答案）
        
        Args:
            file_path: Path to JSONL file / JSONL 文件路径
            limit: Maximum number of problems to load / 最多加载的问题数量
            
        Returns:
            List of problem dictionaries / 问题字典列表
        """
        problems = []  # 存储问题列表 / Store problem list
        with open(file_path, 'r', encoding='utf-8') as f:
            # 逐行读取JSONL文件 / Read JSONL file line by line
            for i, line in enumerate(f):
                # 如果达到限制数量则停止 / Stop if limit reached
                if limit and i >= limit:
                    break
                # 解析JSON行 / Parse JSON line
                data = json.loads(line.strip())

                # 提取最终答案（在 #### 之后）/ Extract final answer (after ####)
                answer_text = data['answer']
                # 分割并获取 #### 后的答案 / Split and get answer after ####
                final_answer = answer_text.split('####')[-1].strip() if '####' in answer_text else answer_text

                # 添加到问题列表 / Add to problem list
                problems.append({
                    'id': f'gsm8k_{i}',           # 问题ID / Problem ID
                    'question': data['question'],  # 问题文本 / Question text
                    'answer': final_answer,        # 最终答案 / Final answer
                    'full_solution': answer_text   # 完整解答 / Full solution
                })

        return problems  # 返回问题列表 / Return problem list 

    @staticmethod
    def load_math(file_path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load MATH dataset / 加载 MATH 数据集
        
        MATH is a competition-level math problem dataset in JSON format.
        MATH 是竞赛级数学问题数据集，JSON 格式。
        
        Each item contains:
        每个项目包含：
        - problem: The math problem / 数学问题
        - answer: The final answer / 最终答案
        - solution: Step-by-step solution / 逐步解答
        - subject: Math subject (e.g., algebra, geometry) / 数学科目（如代数、几何）
        - level: Difficulty level / 难度等级
        
        Args:
            file_path: Path to JSON file / JSON 文件路径
            limit: Maximum number of problems to load / 最多加载的问题数量
            
        Returns:
            List of problem dictionaries / 问题字典列表
        """
        # 加载JSON文件 / Load JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 如果指定了限制，则截取 / Apply limit if specified
        if limit:
            data = data[:limit]

        problems = []  # 存储问题列表 / Store problem list
        # 遍历每个问题 / Iterate through each problem
        for item in data:
            problems.append({
                'id': item.get('unique_id', f"math_{len(problems)}"),  # 问题ID / Problem ID
                'question': item['problem'],      # 问题文本 / Question text
                'answer': item['answer'],         # 答案 / Answer
                'solution': item.get('solution', ''),  # 解答 / Solution
                'subject': item.get('subject', ''),    # 科目 / Subject
                'level': item.get('level', '')         # 难度 / Level
            })

        return problems  # 返回问题列表 / Return problem list 

    @staticmethod
    def load_mydata(file_path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load MyData dataset / 加载 MyData 数据集
        
        MyData is a custom dataset with flexible structure.
        MyData 是具有灵活结构的自定义数据集。
        
        Features / 特点：
        - Supports list or string for final_answer / 支持列表或字符串格式的最终答案
        - Solution is stored as list of steps / 解答存储为步骤列表
        - Includes subfield and context metadata / 包含子领域和上下文元数据
        
        Args:
            file_path: Path to JSON file / JSON 文件路径
            limit: Maximum number of problems to load / 最多加载的问题数量
            
        Returns:
            List of problem dictionaries / 问题字典列表
        """
        # 加载JSON文件 / Load JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 如果指定了限制，则截取 / Apply limit if specified
        if limit:
            data = data[:limit]

        problems = []  # 存储问题列表 / Store problem list
        # 遍历每个问题 / Iterate through each problem
        for item in data:
            # 处理最终答案（可能是列表或字符串）/ Handle final answer (may be list or string)
            final_answer = item['final_answer']
            if isinstance(final_answer, list):
                # 如果是列表，取第一个元素 / If list, take first element
                final_answer = final_answer[0] if final_answer else ""

            # 将解答列表合并为文本 / Join solution list into text
            solution_text = '\n'.join(item.get('solution', []))

            problems.append({
                'id': f"mydata_{item['id']}",     # 问题ID / Problem ID
                'question': item['question'],     # 问题文本 / Question text
                'answer': final_answer,           # 最终答案 / Final answer
                'solution': solution_text,        # 解答步骤 / Solution steps
                'subfield': item.get('subfield', ''),  # 子领域 / Subfield
                'context': item.get('context', '')     # 上下文信息 / Context information
            })

        return problems  # 返回问题列表 / Return problem list

    @staticmethod
    def load_omnimath(file_path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Load Omni-MATH dataset / 加载 Omni-MATH 数据集

        Omni-MATH is a comprehensive math reasoning dataset in JSONL format.
        Format is similar to GSM8K with 'question' and 'answer' fields.
        Omni-MATH 是一个全面的数学推理数据集，JSONL 格式。
        格式类似 GSM8K，包含 'question' 和 'answer' 字段。

        Features / 特点：
        - Comprehensive coverage of math topics / 全面覆盖数学主题
        - Answer format uses '####' separator like GSM8K / 答案格式像GSM8K一样使用'####'分隔符

        Args:
            file_path: Path to Omni-MATH JSONL file
                      Omni-MATH JSONL 文件路径
            limit: Maximum number of problems to load
                   最多加载的问题数量

        Returns:
            List of problem dictionaries
            问题字典列表
        """
        problems = []  # 存储问题列表 / Store problem list
        with open(file_path, 'r', encoding='utf-8') as f:
            # 逐行读取JSONL文件 / Read JSONL file line by line
            for i, line in enumerate(f):
                # 如果达到限制数量则停止 / Stop if limit reached
                if limit and i >= limit:
                    break

                # 解析JSON行 / Parse JSON line
                data = json.loads(line.strip())

                # Extract final answer from "#### answer" format
                # 从 "#### answer" 格式中提取最终答案
                answer_text = data.get('answer', '')
                final_answer = answer_text.split('####')[-1].strip() if '####' in answer_text else answer_text

                # 添加到问题列表 / Add to problem list
                problems.append({
                    'id': f'omnimath_{i}',        # 问题ID / Problem ID
                    'question': data['question'],  # 问题文本 / Question text
                    'answer': final_answer,        # 最终答案 / Final answer
                    'full_solution': answer_text   # 完整解答 / Full solution
                })

        return problems  # 返回问题列表 / Return problem list

    @staticmethod
    # OlympiadBench loader: supports text-only and multi-modal variants
    def load_olympiadbench(
        file_path: str,
        limit: Optional[int] = None,
        filter_multimodal: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Load OlympiadBench dataset / 加载 OlympiadBench 数据集

        OlympiadBench is an Olympiad-level math and physics dataset supporting multi-modal problems.
        Some problems contain images marked as <img_XXXX> in the question text.

        OlympiadBench 是奥林匹克级别的数学和物理数据集，支持多模态问题。
        部分问题在问题文本中包含 <img_XXXX> 标记的图片。

        File naming convention: {ProblemType}_{Modality}_{Subject}_{Language}_{Exam}.json
        - ProblemType: TP (Theorem Proving) or OE (Open-Ended)
        - Modality: TO (Text-Only) or MM (Multi-Modal)
        - Subject: maths or physics
        - Language: en or zh
        - Exam: COMP (Competition) or CEE (College Entrance Exam)

        文件命名规则: {问题类型}_{模态}_{学科}_{语言}_{考试}.json
        - 问题类型: TP (定理证明) 或 OE (开放式)
        - 模态: TO (纯文本) 或 MM (多模态)
        - 学科: maths (数学) 或 physics (物理)
        - 语言: en (英语) 或 zh (中文)
        - 考试: COMP (竞赛) 或 CEE (高考)

        Args:
            file_path: Path to OlympiadBench JSON file
                      OlympiadBench JSON 文件路径
            limit: Maximum number of problems to load
                   最多加载的问题数量
            filter_multimodal: If True, only load multi-modal problems;
                             If False, only load text-only problems;
                             If None, load all problems
                             如果为 True，只加载多模态问题；
                             如果为 False，只加载纯文本问题；
                             如果为 None，加载所有问题

        Returns:
            List of problem dictionaries with multi-modal metadata
            包含多模态元数据的问题字典列表
        """
        # Load JSON data
        # 加载 JSON 数据
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Parse file name to extract metadata
        # 解析文件名以提取元数据（从文件名中提取数据集类型信息）
        file_name = Path(file_path).stem  # 例如："TP_MM_maths_en_COMP" / e.g., "TP_MM_maths_en_COMP"
        parts = file_name.split('_')  # 按下划线分割 / Split by underscore
        if len(parts) >= 5:
            problem_type = parts[0]  # TP（定理证明）或 OE（开放式）/ TP (Theorem Proving) or OE (Open-Ended)
            modality = parts[1]      # TO（纯文本）或 MM（多模态）/ TO (Text-Only) or MM (Multi-Modal)
            subject = parts[2]       # maths（数学）或 physics（物理）/ maths or physics
            language = parts[3]      # en（英语）或 zh（中文）/ en (English) or zh (Chinese)
            exam_type = parts[4]     # COMP（竞赛）或 CEE（高考）/ COMP (Competition) or CEE (College Entrance Exam)
        else:
            # 如果文件名格式不符合预期，使用默认值 / If filename format is unexpected, use defaults
            problem_type = modality = subject = language = exam_type = "unknown"

        problems = []  # 存储问题列表 / Store problem list
        for item in data:
            # 如果达到限制数量则停止 / Stop if limit reached
            if limit and len(problems) >= limit:
                break

            # Check for images in question text
            # 检查问题文本中是否有图片（多模态问题检测）
            question_text = item.get('question', '')
            image_pattern = r'<img_(\d+)>'  # 图片标记模式 / Image marker pattern
            image_matches = re.findall(image_pattern, question_text)  # 查找所有图片标记 / Find all image markers
            has_images = len(image_matches) > 0  # 是否包含图片 / Whether contains images

            # Apply multi-modal filter if specified
            # 应用多模态过滤器（如果指定）
            if filter_multimodal is not None:
                if filter_multimodal and not has_images:
                    continue  # 跳过纯文本问题 / Skip text-only problems
                if not filter_multimodal and has_images:
                    continue  # 跳过多模态问题 / Skip multi-modal problems

            # Extract solution text
            # 提取解答文本（将列表格式的解答合并为字符串）
            solution_list = item.get('solution', [])
            if isinstance(solution_list, list):
                solution_text = '\n\n'.join(solution_list)  # 用双换行连接步骤 / Join steps with double newline
            else:
                solution_text = str(solution_list)  # 转换为字符串 / Convert to string

            # Extract final answer (may be None for proof problems)
            # 提取最终答案（证明题可能为 None）
            final_answer = item.get('final_answer', None)
            if final_answer is None or final_answer == "":
                # For proof problems, use a placeholder
                # 对于证明题，使用占位符（因为证明题没有数值答案）
                final_answer = "[PROOF_REQUIRED]"

            # 添加到问题列表（包含丰富的元数据）/ Add to problem list (with rich metadata)
            problems.append({
                'id': f"olympiad_{item.get('id', len(problems))}",  # 问题ID / Problem ID
                'question': question_text,        # 问题文本 / Question text
                'answer': str(final_answer),      # 最终答案 / Final answer
                'solution': solution_text,        # 解答步骤 / Solution steps
                'subfield': item.get('subfield', ''),  # 子领域 / Subfield
                'context': item.get('context', ''),     # 上下文 / Context
                # Multi-modal metadata / 多模态元数据
                'has_images': has_images,         # 是否包含图片 / Whether contains images
                'image_ids': image_matches if has_images else [],  # 图片ID列表 / List of image IDs
                'image_count': len(image_matches),  # 图片数量 / Number of images
                # Dataset metadata / 数据集元数据
                'problem_type': problem_type,     # 问题类型（TP/OE）/ Problem type (TP/OE)
                'modality': modality,             # 模态（TO/MM）/ Modality (TO/MM)
                'subject': subject,               # 学科（数学/物理）/ Subject (maths/physics)
                'language': language,             # 语言（英语/中文）/ Language (en/zh)
                'exam_type': exam_type,           # 考试类型（竞赛/高考）/ Exam type (COMP/CEE)
                'is_multiple_answer': item.get('is_multiple_answer', False),  # 是否多答案 / Whether multiple answers
                'answer_type': item.get('answer_type', None),  # 答案类型 / Answer type
                'unit': item.get('unit', None)    # 单位 / Unit
            })

        # Print summary / 打印摘要（显示加载的数据集统计信息）
        if problems:
            mm_count = sum(1 for p in problems if p['has_images'])  # 统计多模态问题数 / Count multi-modal problems
            to_count = len(problems) - mm_count  # 统计纯文本问题数 / Count text-only problems
            print(f"\n📊 OlympiadBench Dataset Loaded / OlympiadBench 数据集已加载:")
            print(f"  Total problems: {len(problems)} / 总问题数: {len(problems)}")
            print(f"  Multi-modal (with images): {mm_count} / 多模态（含图片）: {mm_count}")
            print(f"  Text-only: {to_count} / 纯文本: {to_count}")
            print(f"  Subject: {subject} | Language: {language} | Type: {problem_type}\n")

        return problems  # 返回问题列表 / Return problem list


class BaselineEvaluator:
    """
    Baseline methods evaluator
    基线方法评估器

    This class now uses modular baseline implementations from the baselines package.
    该类使用 baselines 包中的模块化基线实现。
    
    Purpose / 目的：
    - Provides baseline solving methods for comparison / 提供用于对比的基线求解方法
    - Wraps three standard approaches: Direct LLM, Zero-shot CoT, Few-shot CoT
      封装三种标准方法：直接LLM、零样本CoT、少样本CoT
    - Extracts final answers from LLM responses / 从LLM响应中提取最终答案
    """

    def __init__(self, llm_client=None):
        """Initialize baseline evaluator / 初始化基线评估器
        
        Args:
            llm_client: Optional LLM client instance. If not provided, creates a default one.
                       可选的LLM客户端实例。如果未提供，则创建默认实例。
        """
        # 初始化或使用提供的 LLM 客户端 / Initialize or use provided LLM client
        if llm_client is None:
            from engine.scaffolder import LLMClient
            llm_client = LLMClient()

        # 保存 LLM 客户端引用 / Save LLM client reference
        self.llm_client = llm_client

        # Initialize baseline solvers / 初始化基线求解器
        # 这些求解器都使用相同的 LLM 客户端 / These solvers all use the same LLM client
        self.direct_llm_solver = DirectLLM(llm_client=llm_client)        # 直接LLM求解器 / Direct LLM solver
        self.zero_shot_cot_solver = ZeroShotCoT(llm_client=llm_client)   # 零样本CoT求解器 / Zero-shot CoT solver
        self.few_shot_cot_solver = FewShotCoT(llm_client=llm_client)     # 少样本CoT求解器 / Few-shot CoT solver 

    def direct_llm(self, problem: str) -> str:
        """
        Direct LLM answer / 直接LLM回答

        Uses DirectLLM baseline from baselines/direct_llm.py
        使用 baselines/direct_llm.py 中的 DirectLLM 基线方法
        
        Approach / 方法：
        - Directly asks LLM to solve the problem without reasoning steps
          直接让LLM解决问题，不提供推理步骤
        - Fastest but least accurate baseline / 最快但最不准确的基线
        
        Args:
            problem: The math problem text / 数学问题文本
            
        Returns:
            The predicted answer / 预测的答案
        """
        return self.direct_llm_solver.solve(problem)

    def zero_shot_cot(self, problem: str) -> Tuple[str, str]:
        """
        Zero-shot Chain of Thought / 零样本思维链

        Uses ZeroShotCoT baseline from baselines/zero_shot_cot.py
        使用 baselines/zero_shot_cot.py 中的 ZeroShotCoT 基线方法
        
        Approach / 方法：
        - Prompts LLM to "think step by step" without examples
          提示LLM"逐步思考"，不提供示例
        - Generates reasoning before answering / 在回答前生成推理过程
        
        Args:
            problem: The math problem text / 数学问题文本
            
        Returns:
            Tuple of (predicted_answer, reasoning_steps)
            返回元组：(预测答案, 推理步骤)
        """
        return self.zero_shot_cot_solver.solve(problem)

    def few_shot_cot(self, problem: str) -> Tuple[str, str]:
        """
        Few-shot Chain of Thought / 少样本思维链

        Uses FewShotCoT baseline from baselines/few_shot_cot.py
        使用 baselines/few_shot_cot.py 中的 FewShotCoT 基线方法
        
        Approach / 方法：
        - Provides few examples of step-by-step reasoning
          提供少量逐步推理的示例
        - LLM follows the pattern to solve new problems / LLM遵循模式解决新问题
        - Most accurate baseline but requires examples / 最准确的基线但需要示例
        
        Args:
            problem: The math problem text / 数学问题文本
            
        Returns:
            Tuple of (predicted_answer, reasoning_steps)
            返回元组：(预测答案, 推理步骤)
        """
        return self.few_shot_cot_solver.solve(problem)

    def _extract_answer(self, response: str) -> str:
        """
        Extract final answer from LLM response / 从LLM响应中提取最终答案
        
        This method tries multiple patterns to extract numerical or text answers.
        该方法尝试多种模式来提取数值或文本答案。
        
        Patterns tried / 尝试的模式：
        1. "答案：" or "Answer:" followed by answer / "答案："或"Answer:"后跟答案
        2. "=" followed by number / "="后跟数字
        3. Number at end of line / 行尾的数字
        4. Last line of response (fallback) / 响应的最后一行（备用）
        
        Args:
            response: LLM response text / LLM响应文本
            
        Returns:
            Extracted answer / 提取的答案
        """
        import re
        
        # 尝试多种模式匹配答案 / Try multiple patterns to match answer
        patterns = [
            r'(?:答案|Answer|Final answer)[:：]\s*([^\n]+)',  # "答案:" or "Answer:" pattern
            r'=\s*([0-9\.]+)',           # "= number" pattern / "= 数字" 模式
            r'([0-9\.]+)\s*$'            # 行尾数字 / Number at end of line
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # 如果没有匹配，返回最后一行作为答案 / If no match, return last line as answer
        lines = response.strip().split('\n')
        return lines[-1].strip() if lines else response.strip()


class FrameworkEvaluator:
    """Evaluator for baselines, full framework, and ablations.
    基线、完整框架和消融实验的评估器。

    Responsibilities / 职责：
    - Route a single problem to the requested method
      将单个问题路由到请求的方法
    - Compare predicted vs expected answers (LLM aided fallback)
      比较预测答案和预期答案（LLM辅助备用）
    - Aggregate per‑method statistics across a dataset
      汇总数据集中每种方法的统计信息
    
    Key Features / 主要特性：
    - Supports multiple evaluation methods (baselines + framework + ablations)
      支持多种评估方法（基线+框架+消融）
    - Uses LLM-based answer comparison for flexible matching
      使用基于LLM的答案比较实现灵活匹配
    - Tracks execution time and error handling
      跟踪执行时间和错误处理
    """

    def __init__(self, verbose: bool = False):
        """Initialize evaluator, baselines, and LLM comparator.
        初始化评估器、基线和LLM比较器。

        Args:
            verbose: Print detailed progress if True.
                    如果为True，打印详细进度信息。
        """
        self.verbose = verbose  # 是否打印详细信息 / Whether to print verbose info
        
        # Baseline wrappers (direct/zero-shot/few-shot CoT)
        # 基线包装器（直接LLM/零样本CoT/少样本CoT）
        self.baseline_evaluator = BaselineEvaluator()

        # LLM comparator (used to compare predicted vs expected answers)
        # LLM比较器（用于比较预测答案和预期答案）
        self.answer_comparison_prompt = self._load_answer_comparison_prompt()
        self.llm_client = self.baseline_evaluator.llm_client

    def evaluate_single(
        self,
        problem: Dict[str, Any],
        method: EvaluationMethod
    ) -> EvaluationResult:
        """Evaluate a single problem with a specified method.
        使用指定方法评估单个问题。

        Steps / 步骤：
        - Route to the corresponding solver/ablation by method
          根据方法路由到相应的求解器/消融实验
        - Measure elapsed time for transparency
          测量执行时间以提供透明度
        - Compare predicted vs expected answers and build a result
          比较预测答案和预期答案并构建结果

        Args:
            problem: Problem dictionary containing id, question, answer
                    问题字典，包含id、问题文本、答案
            method: The evaluation method to use
                   要使用的评估方法

        Returns:
            EvaluationResult with prediction, correctness, timing, etc.
            包含预测、正确性、时间等的评估结果
        """
        # 提取问题信息 / Extract problem information
        problem_id = problem['id']        # 问题ID / Problem ID
        question = problem['question']    # 问题文本 / Question text
        expected_answer = problem['answer']  # 预期答案 / Expected answer

        # 初始化变量 / Initialize variables
        start_time = time.time()  # 记录开始时间 / Record start time
        error = None           # 错误信息 / Error message
        predicted_answer = None  # 预测答案 / Predicted answer
        reasoning_steps = None   # 推理步骤 / Reasoning steps

        try:
            # Route based on selected method / 根据选择的方法路由
            if method == EvaluationMethod.DIRECT_LLM:
                # 直接LLM方法 / Direct LLM method
                predicted_answer = self.baseline_evaluator.direct_llm(question)

            elif method == EvaluationMethod.ZERO_SHOT_COT:
                # 零样本思维链方法 / Zero-shot CoT method
                predicted_answer, reasoning_steps = self.baseline_evaluator.zero_shot_cot(question)

            elif method == EvaluationMethod.FEW_SHOT_COT:
                # 少样本思维链方法 / Few-shot CoT method
                predicted_answer, reasoning_steps = self.baseline_evaluator.few_shot_cot(question)

            elif method == EvaluationMethod.FULL_FRAMEWORK:
                # 完整框架方法 / Full framework method
                predicted_answer = self._run_full_framework(question, problem_id, method.value)

            elif method == EvaluationMethod.NO_RETRIEVER:
                # 无检索器消融 / No retriever ablation
                predicted_answer = self._run_without_retriever(question, problem_id, method.value)

            elif method == EvaluationMethod.NO_AI_RETRIEVER:
                # 无AI检索器消融 / No AI retriever ablation
                predicted_answer = self._run_without_ai_retriever(question, problem_id, method.value)

            elif method == EvaluationMethod.NO_SYMBOLIC_EXECUTION:
                # 无符号执行消融（使用LLM计算）/ No symbolic execution ablation (use LLM computation)
                predicted_answer = self._run_without_symbolic_execution(question, problem_id, method.value)

            elif method == EvaluationMethod.NO_VALIDATION:
                # 无验证消融 / No validation ablation
                predicted_answer = self._run_without_validation(question, problem_id, method.value)

        except Exception as e:
            # 捕获任何异常 / Catch any exception
            error = str(e)

        # 计算执行时间 / Calculate execution time
        execution_time = time.time() - start_time

        # Build result object / 构建结果对象
        # 比较答案（如果有预测答案）/ Compare answers (if predicted answer exists)
        is_correct = self._compare_answers(expected_answer, predicted_answer, question) if predicted_answer else False

        # 获取保存的因果脚手架（如果有）/ Get saved causal scaffold (if any)
        causal_scaffold = getattr(self, '_last_causal_scaffold', None)

        # 创建评估结果对象 / Create evaluation result object
        result = EvaluationResult(
            problem_id=problem_id,
            method=method.value,
            problem_text=question,
            expected_answer=expected_answer,
            predicted_answer=str(predicted_answer) if predicted_answer else None,
            is_correct=is_correct,
            execution_time=execution_time,
            error=error,
            reasoning_steps=reasoning_steps,
            causal_scaffold=causal_scaffold  # 添加因果脚手架用于可视化 / Add causal scaffold for visualization
        )

        # Clear temporary scaffold cache between problems
        # 清除临时脚手架缓存（为下一个问题做准备）/ Clear temporary scaffold cache (prepare for next problem)
        self._last_causal_scaffold = None

        return result

    # Full pipeline: retrieval → scaffold → compute (LLM) → synthesis
    def _run_full_framework(self, problem: str, problem_id: str = None, method: str = None) -> Any:
        """Run full causal reasoning framework with GRPO experiences"""
        try:
            from main import CausalReasoningEngine
            from engine import GRPOExperienceManager

            # Initialize engine
            engine = CausalReasoningEngine(
                knowledge_base_path="data/knowledge_base.json",
                verbose=self.verbose,
                use_ai_retriever=True,
                auto_enrich_kb=True,
                min_rules_threshold=5,
                use_multi_agent=True  # Enable multi-agent for experience injection
            )

            # Load and inject GRPO experiences
            try:
                experience_manager = GRPOExperienceManager(
                    experience_dir="data/grpo_experiences",
                    verbose=False
                )
                
                if hasattr(engine, 'scaffolder') and experience_manager:
                    engine.scaffolder.experience_manager = experience_manager
                    if self.verbose:
                        print(f"  ✓ Loaded GRPO experiences for evaluation")
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠️ Could not load GRPO experiences: {e}")

            # Solve problem
            results = engine.solve_problem(
                problem,
                include_validation=False,
                problem_id=problem_id,
                method_name=method
            )

            # Save causal_scaffold for visualization
            self._last_causal_scaffold = results.get('causal_scaffold')

            if results.get('success'):
                return results.get('final_answer')
            else:
                error_msg = results.get('error', 'Unknown error')
                if self.verbose:
                    print(f"  Framework error: {error_msg}")
                raise Exception(error_msg)

        except Exception as e:
            raise Exception(f"Full framework failed: {e}")

    # Ablation: disable both traditional and AI retrievers
    def _run_without_retriever(self, problem: str, problem_id: str = None, method: str = None) -> Any:
        """Run without knowledge retriever /

        """
        try:
            #
            from main import CausalReasoningEngine

            # Mock
            class EmptyRetriever:
                def get_knowledge(self, problem_text):
                    #
                    return []

            #  AI
            engine = CausalReasoningEngine(
                verbose=self.verbose,
                use_ai_retriever=False,  #  AI
                auto_enrich_kb=False
            )
            #
            engine.retriever = EmptyRetriever()
            #  AI  None
            engine.ai_retriever = None

            #
            results = engine.solve_problem(
                problem,
                include_validation=False,
                problem_id=problem_id,
                method_name=method
            )

            # 
            if results.get('success'):
                return results.get('final_answer')
            else:
                # 
                raise Exception(results.get('error', 'Unknown error'))

        except Exception as e:
            # 
            raise Exception(f"No retriever ablation failed: {e}")

    # Ablation: use only traditional retriever (no AI rule generation)
    def _run_without_ai_retriever(self, problem: str, problem_id: str = None, method: str = None) -> Any:
        """Run with traditional retriever only (no AI rule generation)"""
        try:
            from main import CausalReasoningEngine
            from engine import GRPOExperienceManager

            # Initialize engine without AI retriever
            engine = CausalReasoningEngine(
                verbose=self.verbose,
                use_multi_agent=True
            )

            # Load and inject GRPO experiences (still useful even without AI retriever)
            try:
                experience_manager = GRPOExperienceManager(
                    experience_dir="data/grpo_experiences",
                    verbose=False
                )
                
                if hasattr(engine, 'scaffolder') and experience_manager:
                    engine.scaffolder.experience_manager = experience_manager
            except Exception:
                pass  # Silently continue without experiences

            # Solve problem
            results = engine.solve_problem(
                problem,
                include_validation=False,
                problem_id=problem_id,
                method_name=method
            )

            if results.get('success'):
                return results.get('final_answer')
            else:
                raise Exception(results.get('error', 'Unknown error'))

        except Exception as e:
            raise Exception(f"No AI retriever ablation failed: {e}")

    # Ablation: compute via LLM (no symbolic execution)
    def _run_without_symbolic_execution(self, problem: str, problem_id: str = None, method: str = None) -> Any:
        """
        Run without symbolic execution (use LLM for computation based on causal scaffold).
        不使用符号执行运行（基于因果脚手架使用LLM计算）。

        This is a proper ablation that:
        此消融实验：
        - Still uses Knowledge Retrieval / 仍使用知识检索
        - Still uses Causal Scaffolding / 仍使用因果脚手架
        - **Uses LLM Computation** instead of Symbolic Execution / **使用LLM计算**而非符号执行
        - Still uses Synthesis / 仍使用合成

        This tests whether symbolic execution is necessary or LLM computation is sufficient.
        这测试符号执行是否必要，或者LLM计算是否足够。
        """
        try:
            from main import CausalReasoningEngine
            from engine import GRPOExperienceManager

            # Initialize engine with LLM computation mode
            engine = CausalReasoningEngine(
                knowledge_base_path="data/knowledge_base.json",
                verbose=self.verbose,
                use_ai_retriever=True,
                auto_enrich_kb=True,
                min_rules_threshold=2,
                computation_mode="llm",  # KEY: Use LLM computation instead of symbolic execution
                use_multi_agent=True
            )

            # Load and inject GRPO experiences
            try:
                experience_manager = GRPOExperienceManager(
                    experience_dir="data/grpo_experiences",
                    verbose=False
                )
                
                if hasattr(engine, 'scaffolder') and experience_manager:
                    engine.scaffolder.experience_manager = experience_manager
            except Exception:
                pass  # Silently continue without experiences

            # Solve problem using LLM computation
            results = engine.solve_problem(
                problem,
                include_validation=False,
                problem_id=problem_id,
                method_name=method
            )

            if results.get('success'):
                return results.get('final_answer')
            else:
                error_msg = results.get('error', 'Unknown error')
                if self.verbose:
                    print(f"  LLM computation error: {error_msg}")
                raise Exception(error_msg)

        except Exception as e:
            raise Exception(f"No symbolic execution ablation failed: {e}")

    # Ablation: skip synthesis/validation stage
    def _run_without_validation(self, problem: str, problem_id: str = None, method: str = None) -> Any:
        """Run without validation /

        """
        #
        return self._run_full_framework(problem, problem_id, method)

    def _load_answer_comparison_prompt(self) -> str:
        """Load answer comparison prompt from file"""
        prompt_path = Path("prompts/answer_comparison_prompt.txt")
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Fallback to default prompt
            return """You are a scientific answer verification expert. Determine if two answers are equivalent.

EXPECTED ANSWER: {expected_answer}
PREDICTED ANSWER: {predicted_answer}

Respond with exactly: YES or NO
Then provide a brief reason.

YOUR RESPONSE:"""

    def _compare_answers(self, expected: str, predicted: Any, problem_text: str = "") -> bool:
        """Compare expected and predicted answers using LLM with problem context
        使用 LLM 比较预期答案和预测答案（带问题上下文）
        
        Args:
            expected: Expected answer
            predicted: Predicted answer
            problem_text: The original problem text for context
        """
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
                    print(f"  ✓ LLM Answer Comparison: YES")
                    print(f"    Problem: {problem_text[:100]}..." if len(problem_text) > 100 else f"    Problem: {problem_text}")
                    print(f"    Expected: {expected}")
                    print(f"    Predicted: {predicted}")
                    # Extract and show reasoning if available
                    reasoning = response.strip().split('\n', 1)
                    if len(reasoning) > 1:
                        print(f"    Reasoning: {reasoning[1][:150]}..." if len(reasoning[1]) > 150 else f"    Reasoning: {reasoning[1]}")
                return True
            elif response_upper.startswith("NO"):
                if self.verbose:
                    print(f"  ✗ LLM Answer Comparison: NO")
                    print(f"    Problem: {problem_text[:100]}..." if len(problem_text) > 100 else f"    Problem: {problem_text}")
                    print(f"    Expected: {expected}")
                    print(f"    Predicted: {predicted}")
                    # Extract and show reasoning if available
                    reasoning = response.strip().split('\n', 1)
                    if len(reasoning) > 1:
                        print(f"    Reasoning: {reasoning[1][:150]}..." if len(reasoning[1]) > 150 else f"    Reasoning: {reasoning[1]}")
                return False
            else:
                # If LLM response is unclear, fallback to string matching
                print(f"  ⚠ LLM response unclear, using fallback comparison")
                return self._fallback_compare(expected, predicted)

        except Exception as e:
            # If LLM fails, use fallback comparison
            print(f"  ⚠ LLM comparison failed: {e}, using fallback")
            return self._fallback_compare(expected, predicted)

    def _fallback_compare(self, expected: str, predicted: Any) -> bool:
        """Fallback comparison method (simple rule-based) with enhanced unit and scientific notation handling"""
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
                print(f"    ⚠ Fallback comparison error: {e}")
            pass

        # Remove all spaces and try exact match again
        expected_clean = re.sub(r'\s+', '', expected_str)
        predicted_clean = re.sub(r'\s+', '', predicted_str)
        
        if expected_clean == predicted_clean:
            return True

        return False

    def evaluate_dataset(
        self,
        problems: List[Dict[str, Any]],
        methods: List[EvaluationMethod],
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Evaluate dataset with multiple methods
        
        
        """
        # 
        print(f"\n{'='*80}")
        print(f"Evaluating {dataset_name} with {len(methods)} methods on {len(problems)} problems")
        print(f" {dataset_name}  {len(methods)}  {len(problems)} ")
        print(f"{'='*80}\n")

        all_results = {}  # 

        # 
        for method in methods:
            print(f"\n{''*80}")
            print(f"Method: {method.value}")
            print(f": {method.value}")
            print(f"{''*80}")

            method_results = []  # 
            correct_count = 0    # 
            total_time = 0       # 
            error_count = 0      # 

            # Iterate all problems with simple progress output
            for i, problem in enumerate(problems, 1):
                print(f"[{i}/{len(problems)}] {problem['id']}", end=" ")

                # Evaluate one problem via selected method
                result = self.evaluate_single(problem, method)
                method_results.append(result)

                # Update counters and per‑problem status symbol
                if result.is_correct:
                    correct_count += 1
                    print("✓", end="")  # Correct
                elif result.error:
                    error_count += 1
                    print("❌", end="")  # Error
                else:
                    print("✗", end="")  # Incorrect

                # Show time per problem
                print(f" ({result.execution_time:.2f}s)")
                
                # Show current accuracy in real-time
                current_accuracy = (correct_count / i) * 100
                print(f"    Current: {correct_count}/{i} correct ({current_accuracy:.1f}%)")

                # Aggregate total time for method stats
                total_time += result.execution_time

            # Compute method‑level statistics
            accuracy = correct_count / len(problems) if problems else 0
            avg_time = total_time / len(problems) if problems else 0

            # Collect results and stats for this method
            all_results[method.value] = {
                'results': method_results,  # 
                'statistics': {
                    'total': len(problems),           # 
                    'correct': correct_count,         # 
                    'wrong': len(problems) - correct_count - error_count,  # 
                    'errors': error_count,            # 
                    'accuracy': accuracy,             # 
                    'total_time': total_time,         # 
                    'avg_time': avg_time              # 
                }
            }

            # Method summary line
            print(f"\n  Accuracy: {accuracy*100:.2f}% ({correct_count}/{len(problems)})")
            print(f"  : {accuracy*100:.2f}% ({correct_count}/{len(problems)})")
            print(f"  Avg Time: {avg_time:.2f}s")
            print(f"  : {avg_time:.2f}s")

        # 
        return {
            'dataset_name': dataset_name,      # 
            'total_problems': len(problems),   # 
            'methods': all_results,            # 
            'evaluation_time': datetime.now().isoformat()  # 
        }

    def save_results(self, results: Dict[str, Any], output_path: str):
        """Serialize evaluation results to a JSON file.

        The JSON contains per‑method statistics and per‑problem records.
        """
        # 
        serializable_results = {
            'dataset_name': results['dataset_name'],
            'total_problems': results['total_problems'],
            'evaluation_time': results['evaluation_time'],
            'methods': {}
        }

        # 
        for method_name, method_data in results['methods'].items():
            serializable_results['methods'][method_name] = {
                'statistics': method_data['statistics'],
                'results': [asdict(r) for r in method_data['results']]  # asdict
            }

        # 
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)  # 

        # JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)

        print(f"\n Results saved to: {output_file}")  # 

    def print_comparison_table(self, results: Dict[str, Any]):
        """Pretty‑print a compact comparison table across methods."""
        print(f"\n{'='*80}")
        print(f"COMPARISON TABLE / ")
        print(f"{'='*80}")
        print(f"Dataset: {results['dataset_name']}")
        print(f": {results['dataset_name']}\n")

        # 
        print(f"{'Method':<30} {'Accuracy':<15} {'Avg Time':<15}")
        print(f"{'':<30} {'':<15} {'':<15}")
        print(f"{'-'*80}")

        # 
        for method_name, method_data in results['methods'].items():
            stats = method_data['statistics']
            acc_str = f"{stats['accuracy']*100:.2f}%"  # 
            time_str = f"{stats['avg_time']:.2f}s"     # 
            print(f"{method_name:<30} {acc_str:<15} {time_str:<15}")

        print(f"{'='*80}\n")  # 


def main():
    """CLI entry for running dataset evaluation."""
    import argparse

    # Initialize CLI parser

    #  - 
    parser = argparse.ArgumentParser(
        description="Comprehensive Framework Evaluation\n"
    )

    parser.add_argument(
        '--dataset',
        type=str,
        choices=['gsm8k', 'math', 'mydata', 'omnimath', 'olympiad'],  # 新增 omnimath 和 olympiad / Added omnimath and olympiad
        default='gsm8k',
        help='Dataset to evaluate / '
    )

    #  - 
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Limit number of problems / '
    )

    #  - 
    parser.add_argument(
        '--methods',
        type=str,
        nargs='+',
        choices=['baselines', 'ablations', 'all'],
        default=['baselines'],
        help='Evaluation methods / '
    )

    #  - 
    parser.add_argument(
        '--output',
        type=str,
        default='evaluation_results',
        help='Output directory / '
    )

    #  - 
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output / '
    )

    # 
    args = parser.parse_args()

    # Resolve which methods to evaluate
    methods_to_run = []

    # Baselines (and full framework)
    if 'baselines' in args.methods or 'all' in args.methods:
        methods_to_run.extend([
            # EvaluationMethod.DIRECT_LLM,      # LLM
            # EvaluationMethod.ZERO_SHOT_COT,   #
            # EvaluationMethod.FEW_SHOT_COT,    #
            EvaluationMethod.FULL_FRAMEWORK   # 
        ])

    # Ablation variants
    if 'ablations' in args.methods or 'all' in args.methods:
        methods_to_run.extend([
            EvaluationMethod.NO_RETRIEVER,       # 
            EvaluationMethod.NO_AI_RETRIEVER,    # AI
            EvaluationMethod.NO_SYMBOLIC_EXECUTION  # 
        ])

    # Load dataset problems (switch by name)
    loader = DatasetLoader()

    # 加载数据集 / Load dataset
    if args.dataset == 'gsm8k':
        # GSM8K
        dataset_path = "dataset/GSM8K/grade_school_math/data/test.jsonl"
        problems = loader.load_gsm8k(dataset_path, limit=args.limit)
        dataset_name = "GSM8K"
    elif args.dataset == 'math':
        # MATH
        dataset_path = "dataset/Math/test-00000-of-00001.parquet.json"
        problems = loader.load_math(dataset_path, limit=args.limit)
        dataset_name = "MATH"
    elif args.dataset == 'mydata':
        # MyData
        dataset_path = "dataset/mydata/data/2024A.json"
        problems = loader.load_mydata(dataset_path, limit=args.limit)
        dataset_name = "MyData_2024A"
    elif args.dataset == 'omnimath':
        # Omni-MATH（新增 / NEW!）
        dataset_path = "dataset/Omni-MATH/archive/main_test.jsonl"
        problems = loader.load_omnimath(dataset_path, limit=args.limit)
        dataset_name = "Omni-MATH"
    elif args.dataset == 'olympiad':
        # OlympiadBench（新增，多模态支持 / NEW! Multi-Modal）
        # 默认使用英语数学竞赛的纯文本版本 / Default: English math competition text-only
        dataset_path = "dataset/OlympiadBench_Dataset/OlympiadBench_Dataset/data/TP_TO_maths_en_COMP.json"
        problems = loader.load_olympiadbench(dataset_path, limit=args.limit)
        dataset_name = "OlympiadBench"
        print("\n💡 Tip: You can also try multi-modal versions like TP_MM_maths_en_COMP.json")
        print("💡 提示: 你也可以尝试多模态版本，如 TP_MM_maths_en_COMP.json\n")
    else:
        print(f"❌ Unknown dataset: {args.dataset}")
        return 1

    # 
    if not Path(dataset_path).exists():
        print(f" Dataset not found: {dataset_path}")
        return 1

    # 
    evaluator = FrameworkEvaluator(verbose=args.verbose)

    #  - 
    results = evaluator.evaluate_dataset(problems, methods_to_run, dataset_name)

    #  - 
    evaluator.print_comparison_table(results)

    # 
    output_path = f"{args.output}/{dataset_name}_comparison.json"
    evaluator.save_results(results, output_path)

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n  Evaluation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
