"""
因果脚手架模块 - 简化版
将问题文本转换为结构化因果模型JSON计划
"""

import json
import os
import re
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv


class LLMClient:
    """统一的LLM客户端，支持多个API提供商"""

    def __init__(self, provider: Optional[str] = None):
        """
        初始化LLM客户端

        Args:
            provider: API提供商名称 ('siliconflow', 'openai', 'anthropic')
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
            raise ValueError(f"不支持的提供商: {self.provider}")

    def _init_siliconflow(self):
        """初始化SiliconFlow客户端"""
        from openai import OpenAI

        self.client = OpenAI(
            api_key=os.getenv("SILICONFLOW_API_KEY"),
            base_url=os.getenv("SILICONFLOW_API_BASE", "https://api.siliconflow.cn/v1")
        )
        self.model = os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen2.5-72B-Instruct")

    def _init_openai(self):
        """初始化OpenAI客户端"""
        from openai import OpenAI

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")

    def _init_anthropic(self):
        """初始化Anthropic客户端"""
        from anthropic import Anthropic

        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")

    def complete(self, prompt: str, temperature: float = 0.0) -> str:
        """
        生成文本补全

        Args:
            prompt: 输入提示词
            temperature: 采样温度（0.0表示确定性输出）

        Returns:
            生成的文本
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
            raise ValueError(f"不支持的提供商: {self.provider}")


class CausalScaffolder:
    """因果脚手架生成器"""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        prompt_template_path: str = "prompts/scaffolding_prompt_v3.txt",
        max_retries: int = 3,
        retry_delay: float = 2.0
    ):
        """
        初始化因果脚手架器

        Args:
            llm_client: LLM客户端实例
            prompt_template_path: 提示词模板路径
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.llm_client = llm_client or LLMClient()
        self.prompt_template_path = Path(prompt_template_path)
        self.prompt_template = self._load_prompt_template()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout_log = []

    def _load_prompt_template(self) -> str:
        """加载提示词模板"""
        # 先尝试相对路径
        if self.prompt_template_path.exists():
            with open(self.prompt_template_path, 'r', encoding='utf-8') as f:
                return f.read()

        # 再尝试绝对路径
        project_root = Path(__file__).parent.parent
        absolute_path = project_root / self.prompt_template_path

        if absolute_path.exists():
            with open(absolute_path, 'r', encoding='utf-8') as f:
                return f.read()

        raise FileNotFoundError(
            f"找不到提示词模板文件: {self.prompt_template_path}"
        )

    def generate_scaffold(
        self,
        problem_text: str,
        retrieved_knowledge: List[str],
        experiences: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        生成因果脚手架

        Args:
            problem_text: 问题陈述
            retrieved_knowledge: 相关公式和规则列表
            experiences: 先前经验列表

        Returns:
            解析的JSON脚手架字典，失败则返回None
        """
        # 格式化知识列表
        knowledge_str = "\n".join(
            f"{i}. {rule}" for i, rule in enumerate(retrieved_knowledge, 1)
        ) if retrieved_knowledge else ""

        # 格式化经验列表
        if experiences is None:
            experiences = []
        experiences_str = "\n".join(
            f"{i}. {exp}" for i, exp in enumerate(experiences, 1)
        ) if experiences else ""

        # 构造完整提示词
        prompt = self.prompt_template.format(
            retrieved_knowledge=knowledge_str,
            prior_experiences=experiences_str,
            problem_text=problem_text
        )

        # 重试循环
        for attempt in range(1, self.max_retries + 1):
            try:
                if attempt > 1:
                    time.sleep(self.retry_delay)

                # 调用LLM
                response = self.llm_client.complete(prompt, temperature=0.0)

                # 解析JSON
                scaffold = self._extract_json(response)

                if scaffold:
                    return scaffold

            except TimeoutError as e:
                if attempt == self.max_retries:
                    self._log_error(problem_text, "Timeout", str(e))

            except Exception as e:
                if attempt == self.max_retries:
                    self._log_error(problem_text, type(e).__name__, str(e))

        # 所有重试都失败
        return None

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从LLM响应中提取JSON"""
        # 查找JSON代码块
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)

        if json_match:
            json_str = json_match.group(1)
        else:
            # 查找原始JSON对象
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if not json_match:
                return None
            json_str = json_match.group(0)

        # 处理分数格式 (1/3 → "1/3")
        json_str = re.sub(r':\s*(\d+)/(\d+)(\s*[,\}])', r': "\1/\2"\3', json_str)

        try:
            result = json.loads(json_str)

            # 解包problem_analysis
            if isinstance(result, dict) and "problem_analysis" in result:
                result = result["problem_analysis"]

            return result
        except json.JSONDecodeError:
            return None

    def _log_error(self, problem_text: str, error_type: str, error_msg: str):
        """记录错误"""
        error_entry = {
            'problem_text': problem_text[:200] + '...' if len(problem_text) > 200 else problem_text,
            'attempts': self.max_retries,
            'error': f'{error_type}: {error_msg}',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.timeout_log.append(error_entry)

    def validate_scaffold(self, scaffold: Dict[str, Any]) -> bool:
        """
        验证脚手架结构

        Args:
            scaffold: 要验证的脚手架字典

        Returns:
            有效则返回True，否则返回False
        """
        required_keys = ["target_variable", "knowns", "causal_graph", "computation_plan"]

        # 检查必需的键
        if not all(key in scaffold for key in required_keys):
            return False

        # 验证因果图结构
        for link in scaffold.get("causal_graph", []):
            if not all(key in link for key in ["cause", "effect", "rule"]):
                return False

        # 验证计算计划结构
        for step in scaffold.get("computation_plan", []):
            required_step_keys = ["id", "target", "inputs", "description"]
            if not all(key in step for key in required_step_keys):
                return False

        return True

    def get_timeout_log(self) -> List[Dict[str, Any]]:
        """获取超时/错误日志"""
        return self.timeout_log

    def save_timeout_log(self, output_path: str = "timeout_log.json") -> None:
        """保存超时日志到文件"""
        if not self.timeout_log:
            return

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        log_data = {
            'total_errors': len(self.timeout_log),
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'entries': self.timeout_log
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)


# 使用示例
if __name__ == "__main__":
    scaffolder = CausalScaffolder()

    problem = """
    一个质量为10kg的物体初始静止。
    一个恒定的50牛顿力施加在它身上5秒钟。
    它的最终速度是多少？
    """

    knowledge = [
        "牛顿第二定律: 力等于质量乘以加速度 (F=ma)",
        "运动学方程: 最终速度等于初始速度加加速度乘以时间 (v_f = v_i + a*t)"
    ]

    scaffold = scaffolder.generate_scaffold(
        problem_text=problem,
        retrieved_knowledge=knowledge,
        experiences=[]
    )

    if scaffold:
        print("生成的脚手架:")
        print(json.dumps(scaffold, indent=2, ensure_ascii=False))

        is_valid = scaffolder.validate_scaffold(scaffold)
        print(f"\n验证结果: {is_valid}")
    else:
        print("脚手架生成失败")