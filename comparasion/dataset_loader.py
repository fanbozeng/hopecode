"""
Dataset Loader for Comparison Experiments
对比实验数据集加载器

统一的数据集加载接口，消除代码重复
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class DatasetLoader:
    """统一的数据集加载器"""
    
    @staticmethod
    def load_dataset(dataset_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        加载数据集
        
        Args:
            dataset_name: 数据集名称 ('gsm8k', 'math', 'mydata')
            limit: 限制加载的问题数量
            
        Returns:
            问题列表，每个问题包含 id, question, answer
        """
        # 获取项目根目录（相对于此文件）
        project_root = Path(__file__).resolve().parent.parent
        
        dataset_map = {
            'gsm8k': project_root / "dataset/GSM8K/grade_school_math/data/test.jsonl",
            'math': project_root / "dataset/Math/test-00000-of-00001.parquet.json",
            'mydata': project_root / "dataset/mydata/data/2024A.json",
        }
        
        dataset_path = dataset_map.get(dataset_name.lower())
        
        if not dataset_path:
            print(f"❌ Unknown dataset: {dataset_name}")
            print(f"   Available datasets: {', '.join(dataset_map.keys())}")
            return []
        
        if not dataset_path.exists():
            print(f"❌ Dataset file not found: {dataset_path}")
            print(f"💡 Expected path: {dataset_path.absolute()}")
            return []
        
        problems = []
        
        try:
            if dataset_name.lower() == 'gsm8k':
                problems = DatasetLoader._load_gsm8k(dataset_path, limit)
            elif dataset_name.lower() in ['math', 'mydata']:
                problems = DatasetLoader._load_json_dataset(dataset_path, dataset_name, limit)
        
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        return problems
    
    @staticmethod
    def _load_gsm8k(dataset_path: Path, limit: Optional[int]) -> List[Dict[str, Any]]:
        """加载GSM8K数据集（JSONL格式）"""
        problems = []
        with open(dataset_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                data = json.loads(line.strip())
                answer_text = data['answer']
                final_answer = answer_text.split('####')[-1].strip() if '####' in answer_text else answer_text
                problems.append({
                    'id': f'gsm8k_{i}',
                    'question': data['question'],
                    'answer': final_answer
                })
        return problems
    
    @staticmethod
    def _load_json_dataset(dataset_path: Path, dataset_name: str, limit: Optional[int]) -> List[Dict[str, Any]]:
        """加载JSON格式的数据集（MATH, MyData等）"""
        problems = []
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if limit:
                data = data[:limit]
            
            for i, item in enumerate(data):
                problems.append({
                    'id': item.get('unique_id', f"{dataset_name}_{i}"),
                    'question': item.get('problem', item.get('question', '')),
                    'answer': item.get('answer', item.get('final_answer', ''))
                })
        return problems
    
    @staticmethod
    def get_available_datasets() -> List[str]:
        """获取可用的数据集列表"""
        return ['gsm8k', 'math', 'mydata']
    
    @staticmethod
    def validate_dataset_exists(dataset_name: str) -> bool:
        """验证数据集文件是否存在"""
        project_root = Path(__file__).resolve().parent.parent
        dataset_map = {
            'gsm8k': project_root / "dataset/GSM8K/grade_school_math/data/test.jsonl",
            'math': project_root / "dataset/Math/test-00000-of-00001.parquet.json",
            'mydata': project_root / "dataset/mydata/data/2024A.json",
        }
        
        dataset_path = dataset_map.get(dataset_name.lower())
        return dataset_path is not None and dataset_path.exists()

