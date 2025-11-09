"""
Causal Scaffolding Module
因果脚手架模块

This module translates unstructured problem text into a structured JSON plan
representing a Structural Causal Model (SCM). It uses LLM prompts to guide
the planning process.

本模块将非结构化的问题文本转换为表示结构因果模型（SCM）的结构化JSON计划。
它使用LLM提示词来指导规划过程。
"""

import json
import os
import re
import time  # 新增：用于重试延迟 / Added: for retry delay
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv


class LLMClient:
    """
    Unified LLM client supporting multiple API providers.
    支持多个API提供商的统一LLM客户端
    """

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM client.
        初始化LLM客户端

        Args:
            provider: API provider name ('siliconflow', 'openai', 'anthropic')
                      API提供商名称（'siliconflow'、'openai'、'anthropic'）
        """
        load_dotenv()

        self.provider = provider or os.getenv("DEFAULT_PROVIDER", "siliconflow")

        if self.provider == "siliconflow":
            self._init_siliconflow()
        elif self.provider == "openai":
            self._init_openai()
        elif self.provider == "anthropic":
            self._init_anthropic()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _init_siliconflow(self):
        """Initialize SiliconFlow client / 初始化SiliconFlow客户端"""
        from openai import OpenAI

        api_key = os.getenv("SILICONFLOW_API_KEY")
        api_base = os.getenv("SILICONFLOW_API_BASE", "https://api.siliconflow.cn/v1")
        self.model = os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen2.5-72B-Instruct")

        self.client = OpenAI(api_key=api_key, base_url=api_base)
        print(f"Initialized SiliconFlow client with model: {self.model}")
        print(f"已初始化SiliconFlow客户端，模型: {self.model}")

    def _init_openai(self):
        """Initialize OpenAI client / 初始化OpenAI客户端"""
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")

        self.client = OpenAI(api_key=api_key)
        print(f"Initialized OpenAI client with model: {self.model}")
        print(f"已初始化OpenAI客户端，模型: {self.model}")

    def _init_anthropic(self):
        """Initialize Anthropic client / 初始化Anthropic客户端"""
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")

        self.client = Anthropic(api_key=api_key)
        print(f"Initialized Anthropic client with model: {self.model}")
        print(f"已初始化Anthropic客户端，模型: {self.model}")

    def complete(self, prompt: str, temperature: float = 0.0) -> str:
        """
        Generate completion using the configured LLM.
        使用配置的LLM生成补全

        Args:
            prompt: The input prompt
                    输入提示词
            temperature: Sampling temperature (0.0 for deterministic)
                         采样温度（0.0表示确定性输出）

        Returns:
            Generated text completion
            生成的文本补全
        """
        if self.provider in ["siliconflow", "openai"]:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            return response.choices[0].message.content

        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")


class CausalScaffolder:
    """
    Causal Scaffolding Engine that generates structured problem-solving plans.
    生成结构化问题解决计划的因果脚手架引擎

    This class uses LLM prompts to convert natural language problems into
    JSON representations of Structural Causal Models.

    此类使用LLM提示词将自然语言问题转换为结构因果模型的JSON表示。
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        prompt_template_path: str = "prompts/scaffolding_prompt_v3.txt",
        max_retries: int = 3,  # 新增：最大重试次数 / Added: max retry attempts
        retry_delay: float = 2.0  # 新增：重试延迟（秒）/ Added: retry delay in seconds
    ):
        """
        Initialize the causal scaffolder.
        初始化因果脚手架器

        Args:
            llm_client: LLM client instance (creates default if None)
                        LLM客户端实例（如果为None则创建默认实例）
            prompt_template_path: Path to the scaffolding prompt template
                                  脚手架提示词模板的路径
            max_retries: Maximum number of retry attempts for timeout/errors
                        超时/错误时的最大重试次数
            retry_delay: Delay in seconds between retries
                        重试之间的延迟（秒）
        """
        self.llm_client = llm_client or LLMClient()
        self.prompt_template_path = Path(prompt_template_path)
        self.prompt_template = self._load_prompt_template()
        self.max_retries = max_retries  # 新增 / Added
        self.retry_delay = retry_delay  # 新增 / Added
        self.timeout_log = []  # 新增：记录超时的问题 / Added: log timeout problems

    def _load_prompt_template(self) -> str:
        """
        Load the scaffolding prompt template from file.
        

        Returns:
            The prompt template string
            
        """
        # Try relative path first
        if self.prompt_template_path.exists():
            with open(self.prompt_template_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Try absolute path from project root
        project_root = Path(__file__).parent.parent
        absolute_path = project_root / self.prompt_template_path
        
        if absolute_path.exists():
            with open(absolute_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # If file not found, raise error (no fallback)
        raise FileNotFoundError(
            f"Prompt template not found at:\n"
            f"  - Relative path: {self.prompt_template_path}\n"
            f"  - Absolute path: {absolute_path}\n"
            f"Please ensure 'prompts/scaffolding_prompt_v3.txt' exists in project root."
        )

    def generate_scaffold(
        self,
        problem_text: str,
        retrieved_knowledge: List[str],
        experiences: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a structured causal scaffold from problem text with retry mechanism.
        使用重试机制从问题文本生成结构化因果脚手架

        This method constructs a prompt with the problem and retrieved knowledge,
        sends it to the LLM, and parses the JSON response. If timeout or errors occur,
        it will retry up to max_retries times.

        此方法构造包含问题和检索知识的提示词，发送给 LLM 并解析 JSON 响应。
        如果发生超时或错误，将重试最多 max_retries 次。

        Args:
            problem_text: The problem statement
                          问题陈述
            retrieved_knowledge: List of relevant formulas and rules (from RAG)
                                 相关公式和规则列表（来自RAG）
            experiences: List of prior experiences (from GRPO training)
                        先前的经验列表（来自GRPO训练）

        Returns:
            Parsed JSON scaffold as a dictionary, or None if all retries fail
            解析的 JSON 脚手架字典，如果所有重试都失败则返回 None
        """
        # Format knowledge as a numbered list
        # 格式化知识为编号列表
        knowledge_str = "\n".join(
            f"{i}. {rule}" for i, rule in enumerate(retrieved_knowledge, 1)
        ) if retrieved_knowledge else "No additional knowledge provided."
        
        # Format experiences as a numbered list
        # 格式化经验为编号列表
        if experiences is None:
            experiences = []
        experiences_str = "\n".join(
            f"{i}. {exp}" for i, exp in enumerate(experiences, 1)
        ) if experiences else "No prior experiences available."

        # Construct the full prompt
        # 构造完整的提示词
        prompt = self.prompt_template.format(
            retrieved_knowledge=knowledge_str,
            prior_experiences=experiences_str,
            problem_text=problem_text
        )

        print("Generating causal scaffold...")
        print("生成因果脚手架...")

        # Retry loop / 重试循环
        for attempt in range(1, self.max_retries + 1):
            try:
                # Print attempt info / 打印尝试信息
                if attempt > 1:
                    print(f"\n🔄 Retry attempt {attempt}/{self.max_retries}")
                    print(f"🔄 重试第 {attempt}/{self.max_retries} 次")
                    time.sleep(self.retry_delay)  # Wait before retry / 重试前等待

                print(f"Calling LLM (attempt {attempt})...")
                print(f"调用 LLM（第 {attempt} 次尝试）...")

                # Call LLM with timeout handling / 调用 LLM 并处理超时
                response = self.llm_client.complete(prompt, temperature=0.0)

                print(f"✓ LLM response received ({len(response)} characters)")
                print(f"✓ 已收到 LLM 响应（{len(response)} 字符）")
                print("\n" + "="*80)
                print("LLM Response Preview (first 500 chars):")
                print("LLM 响应预览（前 500 字符）:")
                print("="*80)
                print(response)
                print("="*80 + "\n")

                # Extract JSON from response / 从响应中提取 JSON
                scaffold = self._extract_json(response)

                if scaffold:
                    print("[OK] Successfully generated causal scaffold.")
                    print("[OK] 成功生成因果脚手架")
                    print(f"  Target variable: {scaffold.get('target_variable')}")
                    print(f"  目标变量: {scaffold.get('target_variable')}")
                    print(f"  Knowns: {list(scaffold.get('knowns', {}).keys())}")
                    print(f"  已知量: {list(scaffold.get('knowns', {}).keys())}")
                    return scaffold
                else:
                    # Failed to parse JSON, but might retry / 解析 JSON 失败，但可能重试
                    print(f"\n⚠ Failed to parse JSON (attempt {attempt}/{self.max_retries})")
                    print(f"⚠ 解析 JSON 失败（第 {attempt}/{self.max_retries} 次尝试）")

                    if attempt < self.max_retries:
                        print(f"Will retry in {self.retry_delay} seconds...")
                        print(f"将在 {self.retry_delay} 秒后重试...")
                        continue
                    else:
                        print("\n❌ All retry attempts exhausted for JSON parsing.")
                        print("❌ JSON 解析的所有重试次数已用尽")
                        print("\nFull LLM response:")
                        print("完整 LLM 响应:")
                        print("="*80)
                        print(response)
                        print("="*80)

            except TimeoutError as e:
                # Timeout error - retry / 超时错误 - 重试
                print(f"\n⏱ Timeout error on attempt {attempt}/{self.max_retries}: {e}")
                print(f"⏱ 第 {attempt}/{self.max_retries} 次尝试超时: {e}")

                if attempt < self.max_retries:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    print(f"将在 {self.retry_delay} 秒后重试...")
                else:
                    # Log timeout problem / 记录超时问题
                    timeout_entry = {
                        'problem_text': problem_text[:200] + '...' if len(problem_text) > 200 else problem_text,
                        'attempts': self.max_retries,
                        'error': 'Timeout',
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.timeout_log.append(timeout_entry)

                    print(f"\n❌ TIMEOUT: Failed after {self.max_retries} attempts.")
                    print(f"❌ 超时: {self.max_retries} 次尝试后失败")
                    print(f"Problem logged to timeout_log (total: {len(self.timeout_log)} timeouts)")
                    print(f"问题已记录到 timeout_log（总计: {len(self.timeout_log)} 个超时）")

            except Exception as e:
                # Other errors - retry / 其他错误 - 重试
                error_type = type(e).__name__
                print(f"\n❗ Error on attempt {attempt}/{self.max_retries} ({error_type}): {e}")
                print(f"❗ 第 {attempt}/{self.max_retries} 次尝试出错（{error_type}）: {e}")

                if attempt < self.max_retries:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    print(f"将在 {self.retry_delay} 秒后重试...")
                else:
                    # Log error problem / 记录错误问题
                    error_entry = {
                        'problem_text': problem_text[:200] + '...' if len(problem_text) > 200 else problem_text,
                        'attempts': self.max_retries,
                        'error': f'{error_type}: {str(e)}',
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.timeout_log.append(error_entry)

                    print(f"\n❌ ERROR: Failed after {self.max_retries} attempts.")
                    print(f"❌ 错误: {self.max_retries} 次尝试后失败")
                    print(f"Problem logged to timeout_log (total: {len(self.timeout_log)} errors)")
                    print(f"问题已记录到 timeout_log（总计: {len(self.timeout_log)} 个错误）")

                    import traceback
                    print("\nFull traceback:")
                    print("完整错误追踪:")
                    traceback.print_exc()

        # All retries failed / 所有重试都失败了
        return None

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract and parse JSON from LLM response text.
         LLM  JSON

        Args:
            text: LLM response text that may contain JSON
                   JSON  LLM

        Returns:
            Parsed JSON as dictionary, or None if extraction fails
             JSON  None
        """
        print("Extracting JSON from response...")

        # Try to find JSON code block
        #  JSON
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)

        if json_match:
            json_str = json_match.group(1)
            print("  Found JSON in code block (```json...```)")
        else:
            # Try to find raw JSON object
            #  JSON
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                print("  Found raw JSON object")
            else:
                print("  ❌ No JSON found in response!")
                print("  ❌ JSON！")
                return None

        # Preprocess: Fix Python-style fractions to string format (preserve precision)
        # 预处理：将Python风格的分数转换为字符串格式（保留精度）
        print("  Preprocessing: Converting fractions to string format (e.g., 1/3 → \"1/3\")...")
        
        # Convert patterns like `: 1/3,` to `: "1/3",` to keep precision
        # 将 `: 1/3,` 转换为 `: "1/3",` 以保留精度
        original_json = json_str
        json_str = re.sub(r':\s*(\d+)/(\d+)(\s*[,\}])', r': "\1/\2"\3', json_str)
        json_str = re.sub(r'\[\s*(\d+)/(\d+)(\s*[,\]])', r'["\1/\2"\3', json_str)
        json_str = re.sub(r',\s*(\d+)/(\d+)(\s*[,\]\}])', r', "\1/\2"\3', json_str)
        
        if json_str != original_json:
            print("  ✓ Converted Python-style fractions to JSON strings")

        # Parse JSON
        #  JSON
        try:
            print(f"  Parsing JSON ({len(json_str)} characters)...")
            result = json.loads(json_str)
            print("  ✓ JSON parsed successfully")

            # Check if the result has a "problem_analysis" wrapper and unwrap it
            # 检查结果是否有 "problem_analysis" 包装，如果有则解包
            if isinstance(result, dict) and "problem_analysis" in result:
                print("  📦 Detected 'problem_analysis' wrapper, unwrapping...")
                print("  📦 检测到 'problem_analysis' 包装，正在解包...")
                result = result["problem_analysis"]

            return result
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON parsing error: {e}")
            print(f"❌ JSON : {e}")
            print(f"  Error at line {e.lineno}, column {e.colno}")
            print(f"  : {e.lineno}，{e.colno}")
            print("\nProblematic JSON (first 1000 chars):")
            print("="*80)
            print(json_str[:1000])
            print("="*80)
            return None

    def validate_scaffold(self, scaffold: Dict[str, Any]) -> bool:
        """
        Validate the structure of a generated scaffold.
        验证生成的脚手架结构

        Args:
            scaffold: The scaffold dictionary to validate
                      要验证的脚手架字典

        Returns:
            True if valid, False otherwise
            有效则返回 True，否则返回 False
        """
        required_keys = ["target_variable", "knowns", "causal_graph", "computation_plan"]

        # Check required keys
        # 检查必需的键
        if not all(key in scaffold for key in required_keys):
            print("Missing required keys in scaffold.")
            print("脚手架中缺少必需的键")
            return False

        # Validate causal_graph structure
        # 验证 causal_graph 结构
        for link in scaffold.get("causal_graph", []):
            if not all(key in link for key in ["cause", "effect", "rule"]):
                print("Invalid causal_graph structure.")
                print("causal_graph 结构无效")
                return False

        # Validate computation_plan structure
        # 验证 computation_plan 结构
        for step in scaffold.get("computation_plan", []):
            # New schema: only requires id, target, inputs, description
            # 新schema：只需要 id, target, inputs, description
            required_step_keys = ["id", "target", "inputs", "description"]
            if not all(key in step for key in required_step_keys):
                print(f"Invalid computation_plan structure. Missing keys in step: {step}")
                print(f"computation_plan 结构无效。步骤中缺少键: {step}")
                print(f"Required keys: {required_step_keys}")
                print(f"必需的键: {required_step_keys}")
                return False

        print("Scaffold validation passed.")
        print("脚手架验证通过")
        return True

    def get_timeout_log(self) -> List[Dict[str, Any]]:
        """
        Get the timeout/error log.
        获取超时/错误日志

        Returns:
            List of timeout/error entries
            超时/错误条目列表
        """
        return self.timeout_log

    def save_timeout_log(self, output_path: str = "timeout_log.json") -> None:
        """
        Save timeout/error log to a JSON file.
        将超时/错误日志保存到 JSON 文件

        Args:
            output_path: Path to save the log file
                        保存日志文件的路径
        """
        if not self.timeout_log:
            print("No timeout/error logs to save.")
            print("没有超时/错误日志需要保存")
            return

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        log_data = {
            'total_timeouts': len(self.timeout_log),
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'entries': self.timeout_log
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"\n📝 Timeout log saved to: {output_file}")
        print(f"📝 超时日志已保存到: {output_file}")
        print(f"   Total entries: {len(self.timeout_log)}")
        print(f"   总条目数: {len(self.timeout_log)}")

    def print_timeout_summary(self) -> None:
        """
        Print a summary of timeout/error statistics.
        打印超时/错误统计摘要
        """
        if not self.timeout_log:
            print("\n✓ No timeouts or errors occurred.")
            print("✓ 未发生超时或错误")
            return

        print(f"\n{'='*80}")
        print(f"Timeout/Error Summary / 超时/错误摘要")
        print(f"{'='*80}")
        print(f"Total problems failed: {len(self.timeout_log)}")
        print(f"失败问题总数: {len(self.timeout_log)}")

        # Count error types
        # 统计错误类型
        error_types = {}
        for entry in self.timeout_log:
            error = entry['error']
            error_types[error] = error_types.get(error, 0) + 1

        print(f"\nError types / 错误类型:")
        for error_type, count in error_types.items():
            print(f"  {error_type}: {count}")

        print(f"\nRecent failures / 最近的失败:")
        for i, entry in enumerate(self.timeout_log[-5:], 1):
            print(f"  {i}. [{entry['timestamp']}] {entry['error']}")
            print(f"     Problem: {entry['problem_text'][:100]}...")

        print(f"{'='*80}\n")



# Example usage / 
if __name__ == "__main__":
    # Initialize scaffolder / 
    scaffolder = CausalScaffolder()

    # Test problem / 
    problem = """
    An object with a mass of 10 kg is initially at rest.
    A constant force of 50 Newtons is applied to it for 5 seconds.
    What is its final velocity?
    """

    # Mock retrieved knowledge / 
    knowledge = [
        "Newton's Second Law: Force equals mass times acceleration (F=ma).",
        "Kinematic Equation: Final velocity equals initial velocity plus acceleration multiplied by time (v_f = v_i + a*t)."
    ]

    # Generate scaffold / 
    scaffold = scaffolder.generate_scaffold(
        problem_text=problem,
        retrieved_knowledge=knowledge,
        experiences=[]  # No experiences in test
    )

    if scaffold:
        print("\n--- Generated Scaffold ---")
        print(json.dumps(scaffold, indent=2, ensure_ascii=False))

        # Validate / 
        is_valid = scaffolder.validate_scaffold(scaffold)
        print(f"\nValidation result: {is_valid}")
        print(f": {is_valid}")
