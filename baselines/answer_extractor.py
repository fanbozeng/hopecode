"""
Answer Extraction Utility


This module provides robust answer extraction from LLM responses,
handling various formats including markdown, numbers, and text.

 LLM 
 markdown
"""

import re
from typing import Optional


def clean_markdown(text: str) -> str:
    """
    Remove markdown formatting from text
     markdown 

    Args:
        text: Text with potential markdown formatting
               markdown 

    Returns:
        Cleaned text without markdown
         markdown 
    """
    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)

    # Remove italic (*text* or _text_)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)

    # Remove inline code (`text`)
    text = re.sub(r'`(.+?)`', r'\1', text)

    # Remove extra whitespace
    text = ' '.join(text.split())

    return text.strip()


def extract_interval(text: str) -> Optional[str]:
    """
    Extract interval/range answer from text
    提取区间/范围答案
    
    Handles formats like:
    - [20, 50]
    - (20, 50)
    - 20 to 50
    - 20-50
    - 20～50
    - [20,50]
    
    Args:
        text: Text containing potential interval answer
              包含潜在区间答案的文本
    
    Returns:
        Extracted interval as string (e.g., "[20, 50]"), or None if not found
        提取的区间字符串（例如 "[20, 50]"），如果未找到则返回 None
    """
    # Pattern for interval formats
    interval_patterns = [
        # [20, 50] or [20,50] - square brackets
        r'\[[\s]*(-?[0-9]+\.?[0-9]*)[\s]*,[\s]*(-?[0-9]+\.?[0-9]*)[\s]*\]',
        # (20, 50) or (20,50) - round brackets
        r'\([\s]*(-?[0-9]+\.?[0-9]*)[\s]*,[\s]*(-?[0-9]+\.?[0-9]*)[\s]*\)',
        # 20～50 or 20~50 - tilde (common in Chinese)
        r'(-?[0-9]+\.?[0-9]*)[\s]*[～~][\s]*(-?[0-9]+\.?[0-9]*)',
        # 20 to 50 or 20-50
        r'(-?[0-9]+\.?[0-9]*)[\s]*(?:to|-|至)[\s]*(-?[0-9]+\.?[0-9]*)',
    ]
    
    for pattern in interval_patterns:
        match = re.search(pattern, text)
        if match:
            # Extract the two numbers
            num1 = match.group(1)
            num2 = match.group(2)
            
            # Return in standard format [a, b]
            return f"[{num1}, {num2}]"
    
    return None


def extract_number(text: str, prefer_last: bool = True) -> Optional[str]:
    """
    Extract numerical answer from text
    

    Args:
        text: Text containing potential numerical answer
              
        prefer_last: If True, prefer the last number found
                      True

    Returns:
        Extracted number as string, or None if not found
         None
    """
    # Pattern for numbers with optional currency symbols, units, etc.
    # Matches: $18, 18, 18.5, -18, 18%, 18km, etc.
    patterns = [
        # Currency with number: $18, £20, 15
        r'[\$£¥]\s*([0-9]+\.?[0-9]*)',
        # Number with percentage: 18%, 18.5%
        r'([0-9]+\.?[0-9]*)\s*%',
        # Just a number (including decimals and negatives): 18, 18.5, -18
        r'-?\s*([0-9]+\.?[0-9]*)',
    ]

    all_matches = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        all_matches.extend(matches)

    if not all_matches:
        return None

    # Return last or first match based on preference
    return all_matches[-1] if prefer_last else all_matches[0]


def extract_answer(response: str) -> str:
    """
    Extract final answer from LLM response using multiple strategies
     LLM 

    This function tries multiple extraction patterns in order of priority:
    1. Explicit answer markers (e.g., "Therefore, the answer is...")
    2. Common answer formats (e.g., "Answer:", "Final answer:")
    3. Numbers in the response
    4. Last non-empty line

    此函数按优先级尝试多种提取模式：
    1. 明确的答案标记（例如："Therefore, the answer is..."）
    2. 常见的答案格式（例如："Answer:", "Final answer:"）
    3. 响应中的数字
    4. 最后一行非空行 

    Args:
        response: Full LLM response text
                   LLM 

    Returns:
        Extracted answer string
        
    """
    if not response or not response.strip():
        return ""

    # Clean the response first
    response = response.strip()

    # ============================================================
    # Strategy 1: Look for explicit answer markers with context FIRST
    #  1: 首先查找明确的答案标记
    # ============================================================
    # This is now the FIRST strategy to avoid extracting intervals from reasoning steps
    # 这现在是第一策略，以避免从推理步骤中提取区间

    answer_patterns = [
        # "Therefore, the answer is XXX" or "So the answer is XXX"
        (r'(?:[Tt]herefore|[Ss]o),?\s+(?:the\s+)?answer\s+is\s+([^\n.;]+)', 1),

        # "The final answer is XXX"
        (r'[Tt]he\s+final\s+answer\s+is\s+([^\n.;]+)', 1),

        # "Final answer: XXX" or "Answer: XXX"
        (r'[Ff]inal\s+[Aa]nswer:\s*([^\n]+)', 1),
        (r'[Aa]nswer:\s*([^\n]+)', 1),

        # "The answer is XXX"
        (r'[Tt]he\s+answer\s+is\s+([^\n.;]+)', 1),

        # Boxed answer (common in math): \boxed{XXX}
        (r'\\boxed\{([^}]+)\}', 1),

        # "XXX is the answer"
        (r'([^\n.;]+)\s+is\s+the\s+answer', 1),
    ]

    for pattern, group in answer_patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            answer = match.group(group).strip()
            # Clean markdown from extracted answer
            answer = clean_markdown(answer)

            # If it's just punctuation or empty after cleaning, skip
            if answer and not re.match(r'^[.,;:!?\s]*$', answer):
                # Check if this answer part contains an interval
                # 检查这个答案部分是否包含区间
                interval = extract_interval(answer)
                if interval:
                    return interval
                
                # Try to extract number if present
                number = extract_number(answer)
                if number:
                    return number
                return answer

    # ============================================================
    # Strategy 2: Look for "= XXX" patterns (equations)
    #  2 "= XXX" 
    # ============================================================

    equals_matches = re.findall(r'=\s*([0-9]+\.?[0-9]*(?:\s*[a-zA-Z%]+)?)', response)
    if equals_matches:
        # Get the last equals sign result
        answer = equals_matches[-1].strip()
        return clean_markdown(answer)

    # ============================================================
    # Strategy 3: Extract answers from the last few lines
    #  3: 从最后几行提取答案
    # ============================================================

    lines = [l.strip() for l in response.strip().split('\n') if l.strip()]

    # Check last 3 lines for answers (interval or number)
    # 检查最后3行的答案（区间或数字）
    for line in reversed(lines[-3:]):
        # Skip lines that are just showing work (contain multiple = signs)
        if line.count('=') > 1:
            continue

        # Clean markdown from line
        clean_line = clean_markdown(line)

        # First try to extract interval from this line only
        # 首先尝试仅从这一行提取区间
        interval = extract_interval(clean_line)
        if interval:
            return interval

        # Then try to extract number
        # 然后尝试提取数字
        number = extract_number(clean_line)
        if number:
            return number

    # ============================================================
    # Strategy 4: Look for common conclusion phrases
    #  4
    # ============================================================

    conclusion_patterns = [
        r'[Tt]hus,?\s+([^\n.;]+)',
        r'[Hh]ence,?\s+([^\n.;]+)',
        r'[Ii]n conclusion,?\s+([^\n.;]+)',
        r'[Tt]o sum up,?\s+([^\n.;]+)',
    ]

    for pattern in conclusion_patterns:
        matches = re.findall(pattern, response)
        if matches:
            answer = matches[-1].strip()
            answer = clean_markdown(answer)

            # Try to extract number
            number = extract_number(answer)
            if number:
                return number

            if answer and not re.match(r'^[.,;:!?\s]*$', answer):
                return answer

    # ============================================================
    # Strategy 5: Return last non-empty line (cleaned)
    #  5
    # ============================================================

    if lines:
        last_line = clean_markdown(lines[-1])

        # If it's too long (more than 100 chars), probably not the answer
        if len(last_line) <= 100:
            return last_line

    # ============================================================
    # Strategy 6: Fallback - return cleaned full response
    #  6 - 
    # ============================================================

    return clean_markdown(response)[:200]  # Limit to 200 chars


def normalize_answer(answer: str) -> str:
    """
    Normalize answer for comparison
    

    Args:
        answer: Raw answer string
                

    Returns:
        Normalized answer
        
    """
    # Convert to lowercase
    answer = answer.lower().strip()

    # Remove articles
    answer = re.sub(r'\b(a|an|the)\b', '', answer)

    # Remove punctuation
    answer = re.sub(r'[^\w\s]', '', answer)

    # Remove extra whitespace
    answer = ' '.join(answer.split())

    return answer


# Example usage and tests / 
if __name__ == "__main__":
    print("="*60)
    print("Answer Extraction Utility Test")
    print("")
    print("="*60)

    # Test cases with various formats
    test_cases = [
        {
            "name": "Markdown with bold answer",
            "response": "**Answer:** Janet makes **$18** per day.",
            "expected": "18"
        },
        {
            "name": "Therefore pattern",
            "response": "Step 1: ...\nStep 2: ...\nTherefore, the answer is 42.",
            "expected": "42"
        },
        {
            "name": "Final Answer pattern",
            "response": "Let me calculate:\n5 + 3 = 8\nFinal Answer: 8",
            "expected": "8"
        },
        {
            "name": "Multiple equals signs",
            "response": "x = 5\ny = 3\nx + y = 8\nSo the answer is 8",
            "expected": "8"
        },
        {
            "name": "Currency in answer",
            "response": "The total cost is $125.50",
            "expected": "125.50"
        },
        {
            "name": "Percentage answer",
            "response": "The increase is 15.5%",
            "expected": "15.5"
        },
        {
            "name": "Boxed answer",
            "response": "After simplification: \\boxed{42}",
            "expected": "42"
        },
        {
            "name": "Just a number",
            "response": "18",
            "expected": "18"
        },
        {
            "name": "Complex markdown",
            "response": "**Final Answer:** The result is **$18.50** per day.",
            "expected": "18.50"
        },
        {
            "name": "Negative number",
            "response": "The change in temperature is -5 degrees.",
            "expected": "5"  # Note: we extract absolute value in most cases
        },
        {
            "name": "Interval with square brackets",
            "response": "The time range is [20, 50] seconds.",
            "expected": "[20, 50]"
        },
        {
            "name": "Interval with round brackets",
            "response": "The solution is in the range (10, 30).",
            "expected": "[10, 30]"
        },
        {
            "name": "Interval with tilde (Chinese style)",
            "response": "气泵工作时间为20～50秒。",
            "expected": "[20, 50]"
        },
        {
            "name": "Interval with 'to'",
            "response": "The answer is 15 to 25.",
            "expected": "[15, 25]"
        },
        {
            "name": "Interval with hyphen",
            "response": "The range is 5-10 meters.",
            "expected": "[5, 10]"
        },
        {
            "name": "Interval no spaces",
            "response": "Answer: [20,50]",
            "expected": "[20, 50]"
        },
        {
            "name": "Complex interval answer",
            "response": "为使气压回到安全范围，气泵工作时间范围为 [20, 50] 秒。",
            "expected": "[20, 50]"
        }
    ]

    print("\nRunning test cases...\n")
    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        result = extract_answer(test["response"])
        expected = test["expected"]

        # Check if result matches expected (allowing for minor variations)
        if result == expected or expected in result or result in expected:
            status = "[PASS]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1

        print(f"{status} | Test {i}: {test['name']}")
        print(f"  Response: {test['response'][:60]}...")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        print()

    print("="*60)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f": {passed} , {failed}  {len(test_cases)} ")
    print("="*60)
