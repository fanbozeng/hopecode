"""
LLM计算器 - 简化版
使用LLM基于因果脚手架计算答案，替代符号执行
"""

import json
import re
from typing import Dict, Any, Optional
from .scaffolder import LLMClient


class LLMComputer:
    """基于LLM的计算器，使用因果脚手架执行计算"""

    def __init__(self, llm_client: Optional[LLMClient] = None, verbose: bool = False):
        """
        初始化LLM计算器

        Args:
            llm_client: LLM客户端实例
            verbose: 是否打印详细输出
        """
        self.llm_client = llm_client or LLMClient()
        self.verbose = verbose

    def _print(self, message: str) -> None:
        """只在verbose模式下打印消息"""
        if self.verbose:
            print(message)

    def compute_from_scaffold(
        self,
        causal_scaffold: Dict[str, Any],
        problem_text: str
    ) -> Dict[str, Any]:
        """
        使用LLM基于因果脚手架计算答案

        Args:
            causal_scaffold: 包含计算计划的因果脚手架
            problem_text: 原始问题文本

        Returns:
            计算结果字典:
            {
                'success': bool,
                'result': 最终答案,
                'reasoning': 计算步骤,
                'error': 错误信息（失败时）
            }
        """
        try:
            # 从脚手架提取信息
            variables = causal_scaffold.get('variables', {})
            dependencies = causal_scaffold.get('dependencies', {})
            computation_plan = causal_scaffold.get('computation_plan', [])
            target_variable = causal_scaffold.get('target_variable', '')

            self._print(f"计算目标变量: {target_variable}，共{len(computation_plan)}个步骤")

            # 创建计算提示词
            prompt = self._create_computation_prompt(
                problem_text=problem_text,
                causal_scaffold=causal_scaffold,
                variables=variables,
                dependencies=dependencies,
                computation_plan=computation_plan,
                target_variable=target_variable
            )

            # 调用LLM计算
            response = self.llm_client.complete(prompt, temperature=0.0)

            if not response:
                return {
                    'success': False,
                    'result': None,
                    'reasoning': None,
                    'error': 'LLM返回空响应'
                }

            # 提取最终答案
            final_answer = self._extract_final_answer(response)

            if final_answer is None:
                return {
                    'success': False,
                    'result': None,
                    'reasoning': response,
                    'error': '无法提取最终答案'
                }

            self._print(f"计算完成，答案: {final_answer}")

            return {
                'success': True,
                'result': final_answer,
                'reasoning': response,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'result': None,
                'reasoning': None,
                'error': str(e)
            }

    def _create_computation_prompt(
        self,
        problem_text: str,
        causal_scaffold: Dict[str, Any],
        variables: Dict[str, Any],
        dependencies: Dict[str, Any],
        computation_plan: list,
        target_variable: str
    ) -> str:
        """为LLM计算创建结构化提示"""

        # 格式化变量
        variables_str = "\n".join([
            f"  - {name}: {info.get('description', 'N/A')}"
            for name, info in variables.items()
        ])

        # 格式化依赖关系
        dependencies_str = "\n".join([
            f"  - {var} 依赖于: {', '.join(deps)}"
            for var, deps in dependencies.items()
        ])

        # 格式化计算计划
        computation_steps_str = "\n".join([
            f"  {i+1}. {step.get('description', step.get('operation', 'N/A'))}"
            for i, step in enumerate(computation_plan)
        ])

        prompt = f"""你是一个数学计算助手。根据因果脚手架描述的逻辑结构，逐步执行实际的数值计算。

**问题:**
{problem_text}

**因果脚手架:**

**变量:**
{variables_str}

**依赖关系:**
{dependencies_str}

**计算计划:**
{computation_steps_str}

**目标变量:** {target_variable}

---

**说明:**
1. 按照计算计划逐步执行
2. 展示每一步的计算过程
3. 计算需要的中间值
4. 从问题文本中提取数值
5. 仔细进行所有算术运算
6. 提供目标变量 {target_variable} 的最终答案

**输出格式:**
```
步骤 1: [描述]
  计算: [展示计算过程]
  结果: [中间结果]

步骤 2: [描述]
  计算: [展示计算过程]
  结果: [中间结果]

...

最终答案: [{target_variable}的数值]
```

**重要:**
- 最后一行必须是: "最终答案: [数值]"
- 精确进行数值计算
- 清晰展示所有中间步骤

现在开始计算:
"""
        return prompt

    def _extract_final_answer(self, response: str) -> Optional[Any]:
        """
        从LLM响应中提取最终答案

        Args:
            response: LLM响应文本

        Returns:
            最终答案（数字或字符串），未找到则返回None
        """
        # 查找 "最终答案:" 或 "Final Answer:" 模式
        patterns = [
            r'最终答案:\s*([^\n]+)',
            r'Final Answer:\s*([^\n]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                answer_text = match.group(1).strip()
                self._print(f"找到答案: {answer_text}")
                return answer_text

        self._print("未找到答案模式")
        return None


# 导出类
__all__ = ['LLMComputer']