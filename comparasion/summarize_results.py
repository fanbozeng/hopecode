"""
统计汇总工具
Result Summarization Tool

功能 / Features:
1. 读取所有已评估的结果JSON
   Read all evaluated result JSON files
2. 提取 Accuracy、CF、AC
   Extract Accuracy, CF, AC
3. 按方法分组
   Group by method
4. 生成对比表格（Markdown、LaTeX、CSV）
   Generate comparison tables (Markdown, LaTeX, CSV)
5. 生成可视化图表（柱状图、雷达图）
   Generate visualization charts (bar chart, radar chart)
6. 生成统计报告
   Generate statistical report

使用方法 / Usage:
    # 汇总所有结果
    python comparasion/summarize_results.py

    # 指定输出目录
    python comparasion/summarize_results.py --output-dir comparasion/summary

    # 只生成表格（不生成图表）
    python comparasion/summarize_results.py --no-charts

    # 指定数据集
    python comparasion/summarize_results.py --dataset gsm8k
"""

import json
import sys
import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


class ResultSummarizer:
    """结果汇总器 / Result Summarizer"""
    
    def __init__(
        self,
        results_dir: str = "comparasion/results",
        output_dir: str = "comparasion/summary",
        verbose: bool = True
    ):
        """
        初始化汇总器 / Initialize summarizer
        
        Args:
            results_dir: 结果目录 / Results directory
            output_dir: 输出目录 / Output directory
            verbose: 是否显示详细信息 / Whether to show verbose info
        """
        self.results_dir = Path(results_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
    
    def summarize_all(self, generate_charts: bool = True, dataset_filter: Optional[str] = None):
        """
        汇总所有结果 / Summarize all results
        
        Args:
            generate_charts: 是否生成图表 / Whether to generate charts
            dataset_filter: 只汇总指定数据集 / Only summarize specified dataset
        """
        print("="*80)
        print("📊 统计汇总 / Result Summarization")
        print("="*80)
        print(f"📁 Results directory: {self.results_dir}")
        print(f"📁 结果目录: {self.results_dir}")
        print(f"📂 Output directory: {self.output_dir}")
        print(f"📂 输出目录: {self.output_dir}")
        print("="*80 + "\n")
        
        # 1. 收集所有方法的统计数据 / Collect statistics for all methods
        print("🔍 Collecting statistics...")
        print("🔍 收集统计数据...")
        summary_data = self._collect_statistics(dataset_filter)
        
        if not summary_data['methods']:
            print("❌ No evaluated results found!")
            print("❌ 未找到已评估的结果！")
            print("💡 Please run evaluate_cf_ac_batch.py first.")
            print("💡 请先运行 evaluate_cf_ac_batch.py。")
            return
        
        print(f"✅ Found {len(summary_data['methods'])} method(s)")
        print(f"✅ 找到 {len(summary_data['methods'])} 个方法\n")
        
        # 2. 保存原始汇总数据 / Save raw summary data
        print("💾 Saving summary data...")
        print("💾 保存汇总数据...")
        self._save_summary_json(summary_data)
        
        # 3. 生成表格 / Generate tables
        print("📝 Generating tables...")
        print("📝 生成表格...")
        self._generate_markdown_table(summary_data)
        self._generate_latex_table(summary_data)
        self._generate_csv_table(summary_data)
        
        # 4. 生成图表 / Generate charts
        if generate_charts:
            print("📊 Generating charts...")
            print("📊 生成图表...")
            try:
                self._generate_bar_chart(summary_data)
                self._generate_radar_chart(summary_data)
            except ImportError:
                print("⚠️  matplotlib not installed, skipping charts")
                print("⚠️  未安装matplotlib，跳过图表生成")
        
        # 5. 生成详细报告 / Generate detailed report
        print("📄 Generating detailed report...")
        print("📄 生成详细报告...")
        self._generate_detailed_report(summary_data)
        
        # 6. 总结 / Summary
        print("\n" + "="*80)
        print("✅ Summary completed! / 汇总完成！")
        print("="*80)
        print(f"📂 Output directory: {self.output_dir}")
        print(f"📂 输出目录: {self.output_dir}")
        print("\n📄 Generated files / 生成的文件:")
        for file in sorted(self.output_dir.iterdir()):
            print(f"  - {file.name}")
        print("="*80 + "\n")
    
    def _collect_statistics(self, dataset_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        收集所有方法的统计数据 / Collect statistics for all methods
        
        Args:
            dataset_filter: 只收集指定数据集 / Only collect specified dataset
        
        Returns:
            汇总数据字典 / Summary data dictionary
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'dataset_filter': dataset_filter,
            'methods': {}
        }
        
        # 扫描所有方法目录 / Scan all method directories
        for method_dir in self.results_dir.iterdir():
            if not method_dir.is_dir():
                continue
            
            method_name = method_dir.name
            
            # 如果是ablation目录，递归处理子目录 / If ablation directory, process subdirectories
            if method_name == 'ablation':
                for ablation_dir in method_dir.iterdir():
                    if ablation_dir.is_dir():
                        ablation_name = f"cfgo_{ablation_dir.name}"
                        stats = self._extract_method_statistics(ablation_dir, dataset_filter)
                        if stats:
                            summary['methods'][ablation_name] = stats
            else:
                stats = self._extract_method_statistics(method_dir, dataset_filter)
                if stats:
                    summary['methods'][method_name] = stats
        
        return summary
    
    def _extract_method_statistics(
        self,
        method_dir: Path,
        dataset_filter: Optional[str] = None
    ) -> Optional[Dict]:
        """
        提取单个方法的统计数据 / Extract statistics for a single method
        
        Args:
            method_dir: 方法目录 / Method directory
            dataset_filter: 数据集过滤器 / Dataset filter
        
        Returns:
            统计数据字典 / Statistics dictionary
        """
        # 找到所有JSON文件 / Find all JSON files
        json_files = list(method_dir.glob("*.json"))
        if not json_files:
            return None
        
        # 如果指定了数据集过滤，只保留匹配的文件 / Filter by dataset if specified
        if dataset_filter:
            json_files = [f for f in json_files if dataset_filter.lower() in f.name.lower()]
            if not json_files:
                return None
        
        # 按修改时间排序，取最新的 / Sort by modification time, take latest
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        
        # 加载JSON / Load JSON
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error loading {latest_file.name}: {e}")
            return None
        
        # 提取统计数据 / Extract statistics
        stats = data.get('statistics', {})
        
        # 检查是否有CF/AC分数 / Check if CF/AC scores exist
        if 'cf_score' not in stats or 'ac_score' not in stats:
            if self.verbose:
                print(f"⚠️  {latest_file.name} missing CF/AC scores (run evaluate_cf_ac_batch.py first)")
            # 仍然返回数据，但CF/AC为None / Still return data, but CF/AC are None
        
        return {
            'file': latest_file.name,
            'dataset': self._extract_dataset_name(latest_file.name),
            'total_problems': stats.get('total', 0),
            'correct': stats.get('correct', 0),
            'accuracy': stats.get('accuracy', 0.0),
            'cf_score': stats.get('cf_score', None),
            'ac_score': stats.get('ac_score', None),
            'avg_time': stats.get('avg_time', 0.0),
            'total_time': stats.get('total_time', 0.0),
            'errors': stats.get('errors', 0),
        }
    
    def _extract_dataset_name(self, filename: str) -> str:
        """
        从文件名提取数据集名称 / Extract dataset name from filename
        
        Args:
            filename: 文件名 / Filename
        
        Returns:
            数据集名称 / Dataset name
        """
        # 常见数据集名称 / Common dataset names
        datasets = ['gsm8k', 'math', 'mydata', 'omnimath', 'olympiad']
        
        filename_lower = filename.lower()
        for dataset in datasets:
            if dataset in filename_lower:
                return dataset.upper()
        
        return "Unknown"
    
    def _save_summary_json(self, summary_data: Dict):
        """保存原始汇总数据 / Save raw summary data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"summary_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ {output_file.name}")
    
    def _generate_markdown_table(self, summary_data: Dict):
        """生成Markdown表格 / Generate Markdown table"""
        output_file = self.output_dir / "comparison_table.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 方法对比表 / Method Comparison Table\n\n")
            f.write(f"**Generated at / 生成时间**: {summary_data['timestamp']}\n\n")
            
            # 分组：基线方法、CFGO、消融实验
            # Group: Baselines, CFGO, Ablations
            baselines = []
            cfgo_methods = []
            ablations = []
            
            for method_name in summary_data['methods'].keys():
                if method_name in ['direct_llm', 'zero_shot_cot', 'few_shot_cot']:
                    baselines.append(method_name)
                elif method_name == 'cfgo' or method_name == 'cfgo_full':
                    cfgo_methods.append(method_name)
                elif method_name.startswith('cfgo_'):
                    ablations.append(method_name)
                else:
                    cfgo_methods.append(method_name)
            
            # 基线方法表格 / Baseline methods table
            if baselines or cfgo_methods:
                f.write("## 基线方法 vs CFGO / Baselines vs CFGO\n\n")
                f.write("| Method | Dataset | Accuracy | CF Score | AC Score | Avg Time (s) |\n")
                f.write("|--------|---------|----------|----------|----------|-------------|\n")
                
                for method in baselines:
                    if method in summary_data['methods']:
                        stats = summary_data['methods'][method]
                        f.write(self._format_table_row(method, stats))
                
                # CFGO完整版 / CFGO full version
                for method in cfgo_methods:
                    if method in summary_data['methods']:
                        stats = summary_data['methods'][method]
                        display_name = f"**{method.upper()}**"
                        f.write(self._format_table_row(display_name, stats))
            
            # 消融实验表格 / Ablation experiments table
            if ablations:
                f.write("\n## 消融实验 / Ablation Studies\n\n")
                f.write("| Ablation | Dataset | Accuracy | CF Score | AC Score | Avg Time (s) |\n")
                f.write("|----------|---------|----------|----------|----------|-------------|\n")
                
                # 排序：full在最前面 / Sort: full first
                ablations_sorted = sorted(ablations, key=lambda x: (x != 'cfgo_full', x))
                
                for method in ablations_sorted:
                    if method in summary_data['methods']:
                        stats = summary_data['methods'][method]
                        display_name = method.replace('cfgo_', 'CFGO-')
                        f.write(self._format_table_row(display_name, stats))
            
            # 添加说明 / Add notes
            f.write("\n## 说明 / Notes\n\n")
            f.write("- **Accuracy**: 答案正确率 / Answer correctness rate\n")
            f.write("- **CF Score**: 反事实忠实度 (Counterfactual Faithfulness)\n")
            f.write("  - 综合评分 = (因果干预 + 逻辑质量 + 图质量) / 3\n")
            f.write("  - Composite score = (Causal Intervention + Logic Quality + Graph Quality) / 3\n")
            f.write("- **AC Score**: 溯因一致性 (Abductive Consistency)\n")
            f.write("  - 评估答案能否被一致地反向推导\n")
            f.write("  - Evaluates if answer can be consistently reverse-engineered\n")
            f.write("- **Avg Time**: 平均执行时间（秒）/ Average execution time (seconds)\n")
        
        print(f"  ✅ {output_file.name}")
    
    def _format_table_row(self, method_name: str, stats: Dict) -> str:
        """
        格式化表格行 / Format table row
        
        Args:
            method_name: 方法名称 / Method name
            stats: 统计数据 / Statistics
        
        Returns:
            表格行字符串 / Table row string
        """
        dataset = stats.get('dataset', 'N/A')
        accuracy = f"{stats['accuracy']*100:.2f}%" if stats.get('accuracy') is not None else "N/A"
        cf_score = f"{stats['cf_score']:.3f}" if stats.get('cf_score') is not None else "N/A"
        ac_score = f"{stats['ac_score']:.3f}" if stats.get('ac_score') is not None else "N/A"
        avg_time = f"{stats['avg_time']:.2f}" if stats.get('avg_time') is not None else "N/A"
        
        return f"| {method_name} | {dataset} | {accuracy} | {cf_score} | {ac_score} | {avg_time} |\n"
    
    def _generate_latex_table(self, summary_data: Dict):
        """生成LaTeX表格 / Generate LaTeX table"""
        output_file = self.output_dir / "comparison_table.tex"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("% 方法对比表 / Method Comparison Table\n")
            f.write(f"% Generated at: {summary_data['timestamp']}\n\n")
            
            f.write("\\begin{table}[h]\n")
            f.write("\\centering\n")
            f.write("\\caption{方法对比结果 / Method Comparison Results}\n")
            f.write("\\label{tab:method_comparison}\n")
            f.write("\\begin{tabular}{lcccc}\n")
            f.write("\\hline\n")
            f.write("Method & Accuracy & CF Score & AC Score & Avg Time (s) \\\\\n")
            f.write("\\hline\n")
            
            # 基线方法 / Baseline methods
            baselines = ['direct_llm', 'zero_shot_cot', 'few_shot_cot']
            for method in baselines:
                if method in summary_data['methods']:
                    stats = summary_data['methods'][method]
                    f.write(self._format_latex_row(method.replace('_', ' ').title(), stats))
            
            f.write("\\hline\n")
            
            # CFGO / CFGO
            cfgo_methods = ['cfgo', 'cfgo_full']
            for method in cfgo_methods:
                if method in summary_data['methods']:
                    stats = summary_data['methods'][method]
                    f.write(self._format_latex_row('\\textbf{CFGO (Full)}', stats))
                    break
            
            f.write("\\hline\n")
            f.write("\\end{tabular}\n")
            f.write("\\end{table}\n")
        
        print(f"  ✅ {output_file.name}")
    
    def _format_latex_row(self, method_name: str, stats: Dict) -> str:
        """
        格式化LaTeX表格行 / Format LaTeX table row
        
        Args:
            method_name: 方法名称 / Method name
            stats: 统计数据 / Statistics
        
        Returns:
            LaTeX表格行字符串 / LaTeX table row string
        """
        accuracy = f"{stats['accuracy']*100:.2f}\\%" if stats.get('accuracy') is not None else "N/A"
        cf_score = f"{stats['cf_score']:.3f}" if stats.get('cf_score') is not None else "N/A"
        ac_score = f"{stats['ac_score']:.3f}" if stats.get('ac_score') is not None else "N/A"
        avg_time = f"{stats['avg_time']:.2f}" if stats.get('avg_time') is not None else "N/A"
        
        return f"{method_name} & {accuracy} & {cf_score} & {ac_score} & {avg_time} \\\\\n"
    
    def _generate_csv_table(self, summary_data: Dict):
        """生成CSV表格 / Generate CSV table"""
        output_file = self.output_dir / "comparison_table.csv"
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 表头 / Header
            writer.writerow(['Method', 'Dataset', 'Total Problems', 'Correct', 'Accuracy', 'CF Score', 'AC Score', 'Avg Time (s)', 'Total Time (s)', 'Errors'])
            
            # 数据行 / Data rows
            for method_name, stats in sorted(summary_data['methods'].items()):
                writer.writerow([
                    method_name,
                    stats.get('dataset', 'N/A'),
                    stats.get('total_problems', 0),
                    stats.get('correct', 0),
                    f"{stats['accuracy']*100:.2f}" if stats.get('accuracy') is not None else "N/A",
                    f"{stats['cf_score']:.3f}" if stats.get('cf_score') is not None else "N/A",
                    f"{stats['ac_score']:.3f}" if stats.get('ac_score') is not None else "N/A",
                    f"{stats['avg_time']:.2f}" if stats.get('avg_time') is not None else "N/A",
                    f"{stats['total_time']:.2f}" if stats.get('total_time') is not None else "N/A",
                    stats.get('errors', 0)
                ])
        
        print(f"  ✅ {output_file.name}")
    
    def _generate_bar_chart(self, summary_data: Dict):
        """生成柱状图 / Generate bar chart"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            print("  ⚠️  matplotlib not installed, skipping bar chart")
            return
        
        # 准备数据 / Prepare data
        methods = []
        accuracies = []
        cf_scores = []
        ac_scores = []
        
        for method, stats in sorted(summary_data['methods'].items()):
            methods.append(method.replace('_', '\n'))  # 换行以适应图表 / Line break for chart
            accuracies.append(stats['accuracy'] * 100 if stats.get('accuracy') is not None else 0)
            cf_scores.append(stats['cf_score'] * 100 if stats.get('cf_score') is not None else 0)
            ac_scores.append(stats['ac_score'] * 100 if stats.get('ac_score') is not None else 0)
        
        # 创建图表 / Create chart
        x = np.arange(len(methods))
        width = 0.25
        
        fig, ax = plt.subplots(figsize=(14, 7))
        
        bars1 = ax.bar(x - width, accuracies, width, label='Accuracy', color='#3498db')
        bars2 = ax.bar(x, cf_scores, width, label='CF Score', color='#e74c3c')
        bars3 = ax.bar(x + width, ac_scores, width, label='AC Score', color='#2ecc71')
        
        # 添加数值标签 / Add value labels
        def autolabel(bars):
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f'{height:.1f}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom',
                                fontsize=8)
        
        autolabel(bars1)
        autolabel(bars2)
        autolabel(bars3)
        
        # 设置标签和标题 / Set labels and title
        ax.set_xlabel('Method', fontsize=12, fontweight='bold')
        ax.set_ylabel('Score (%)', fontsize=12, fontweight='bold')
        ax.set_title('Method Comparison: Accuracy, CF Score, AC Score', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(methods, rotation=0, ha='center', fontsize=9)
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_ylim(0, 105)
        
        plt.tight_layout()
        output_file = self.output_dir / "comparison_chart.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✅ {output_file.name}")
    
    def _generate_radar_chart(self, summary_data: Dict):
        """生成雷达图 / Generate radar chart"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            print("  ⚠️  matplotlib not installed, skipping radar chart")
            return
        
        # 选择关键方法 / Select key methods
        key_methods = []
        method_priority = ['direct_llm', 'zero_shot_cot', 'few_shot_cot', 'cfgo', 'cfgo_full']
        
        for method in method_priority:
            if method in summary_data['methods']:
                key_methods.append(method)
        
        # 如果没有足够的方法，添加其他方法 / If not enough methods, add others
        for method in summary_data['methods'].keys():
            if method not in key_methods and len(key_methods) < 5:
                key_methods.append(method)
        
        if len(key_methods) < 2:
            print("  ⚠️  Not enough methods for radar chart (need at least 2)")
            return
        
        # 准备数据 / Prepare data
        categories = ['Accuracy', 'CF Score', 'AC Score']
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
        
        for i, method in enumerate(key_methods):
            if method not in summary_data['methods']:
                continue
            
            stats = summary_data['methods'][method]
            values = [
                stats['accuracy'] * 100 if stats.get('accuracy') is not None else 0,
                stats['cf_score'] * 100 if stats.get('cf_score') is not None else 0,
                stats['ac_score'] * 100 if stats.get('ac_score') is not None else 0,
            ]
            values += values[:1]
            
            color = colors[i % len(colors)]
            ax.plot(angles, values, 'o-', linewidth=2, label=method, color=color)
            ax.fill(angles, values, alpha=0.15, color=color)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=12)
        ax.set_ylim(0, 100)
        ax.set_title('Method Comparison (Radar Chart)', fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        output_file = self.output_dir / "radar_chart.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✅ {output_file.name}")
    
    def _generate_detailed_report(self, summary_data: Dict):
        """生成详细报告 / Generate detailed report"""
        output_file = self.output_dir / "detailed_report.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 详细评估报告 / Detailed Evaluation Report\n\n")
            f.write(f"**生成时间 / Generated at**: {summary_data['timestamp']}\n\n")
            f.write("---\n\n")
            
            # 总体统计 / Overall statistics
            f.write("## 总体统计 / Overall Statistics\n\n")
            f.write(f"- **评估方法数 / Number of methods**: {len(summary_data['methods'])}\n")
            
            # 找出最佳方法 / Find best methods
            best_accuracy_method = max(summary_data['methods'].items(), 
                                      key=lambda x: x[1].get('accuracy', 0) or 0)
            f.write(f"- **最高准确率 / Highest accuracy**: {best_accuracy_method[0]} ({best_accuracy_method[1]['accuracy']*100:.2f}%)\n")
            
            # 检查是否有CF/AC分数 / Check if CF/AC scores exist
            methods_with_cf = {k: v for k, v in summary_data['methods'].items() 
                              if v.get('cf_score') is not None}
            
            if methods_with_cf:
                best_cf_method = max(methods_with_cf.items(), 
                                    key=lambda x: x[1].get('cf_score', 0) or 0)
                f.write(f"- **最高CF分数 / Highest CF score**: {best_cf_method[0]} ({best_cf_method[1]['cf_score']:.3f})\n")
                
                best_ac_method = max(methods_with_cf.items(), 
                                    key=lambda x: x[1].get('ac_score', 0) or 0)
                f.write(f"- **最高AC分数 / Highest AC score**: {best_ac_method[0]} ({best_ac_method[1]['ac_score']:.3f})\n")
            
            f.write("\n---\n\n")
            
            # 各方法详细信息 / Detailed information for each method
            f.write("## 各方法详细信息 / Detailed Method Information\n\n")
            
            for method_name, stats in sorted(summary_data['methods'].items()):
                f.write(f"### {method_name}\n\n")
                f.write(f"- **数据集 / Dataset**: {stats.get('dataset', 'N/A')}\n")
                f.write(f"- **来源文件 / Source file**: `{stats.get('file', 'N/A')}`\n")
                f.write(f"- **问题总数 / Total problems**: {stats.get('total_problems', 0)}\n")
                f.write(f"- **正确数 / Correct**: {stats.get('correct', 0)}\n")
                f.write(f"- **准确率 / Accuracy**: {stats['accuracy']*100:.2f}%\n" if stats.get('accuracy') is not None else "- **准确率 / Accuracy**: N/A\n")
                f.write(f"- **CF分数 / CF Score**: {stats['cf_score']:.3f}\n" if stats.get('cf_score') is not None else "- **CF分数 / CF Score**: N/A (需要先运行evaluate_cf_ac_batch.py)\n")
                f.write(f"- **AC分数 / AC Score**: {stats['ac_score']:.3f}\n" if stats.get('ac_score') is not None else "- **AC分数 / AC Score**: N/A (需要先运行evaluate_cf_ac_batch.py)\n")
                f.write(f"- **平均时间 / Avg time**: {stats['avg_time']:.2f}s\n" if stats.get('avg_time') is not None else "- **平均时间 / Avg time**: N/A\n")
                f.write(f"- **总时间 / Total time**: {stats['total_time']:.2f}s\n" if stats.get('total_time') is not None else "- **总时间 / Total time**: N/A\n")
                f.write(f"- **错误数 / Errors**: {stats.get('errors', 0)}\n")
                f.write("\n")
            
            f.write("---\n\n")
            
            # 评估指标说明 / Evaluation metrics explanation
            f.write("## 评估指标说明 / Evaluation Metrics Explanation\n\n")
            f.write("### Accuracy (准确率)\n")
            f.write("- 答案正确的问题数 / 总问题数\n")
            f.write("- Number of correct answers / Total number of problems\n\n")
            
            f.write("### CF Score (反事实忠实度 / Counterfactual Faithfulness)\n")
            f.write("- **综合评分** = (因果干预分数 + 逻辑质量分数 + 图质量分数) / 3\n")
            f.write("- **Composite score** = (Causal Intervention + Logic Quality + Graph Quality) / 3\n")
            f.write("- **因果干预 / Causal Intervention**: 使用do-calculus评估节点重要性\n")
            f.write("- **逻辑质量 / Logic Quality**: LLM评估推理的逻辑连贯性\n")
            f.write("- **图质量 / Graph Quality**: 评估DAG的结构完整性\n\n")
            
            f.write("### AC Score (溯因一致性 / Abductive Consistency)\n")
            f.write("- 评估答案能否被一致地反向推导\n")
            f.write("- Evaluates if the answer can be consistently reverse-engineered\n")
            f.write("- 通过LLM从答案反推问题，检查一致性\n")
            f.write("- Uses LLM to reverse-engineer from answer to problem, checking consistency\n\n")
        
        print(f"  ✅ {output_file.name}")


def main():
    """命令行入口 / CLI entry point"""
    parser = argparse.ArgumentParser(
        description="统计汇总工具 / Result Summarization Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples / 示例:
  # 汇总所有结果
  python comparasion/summarize_results.py

  # 指定输出目录
  python comparasion/summarize_results.py --output-dir comparasion/summary

  # 只生成表格（不生成图表）
  python comparasion/summarize_results.py --no-charts

  # 指定数据集
  python comparasion/summarize_results.py --dataset gsm8k
        """
    )
    
    parser.add_argument(
        '--results-dir',
        type=str,
        default='comparasion/results',
        help='结果目录路径 / Results directory path'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='comparasion/summary',
        help='输出目录路径 / Output directory path'
    )
    
    parser.add_argument(
        '--no-charts',
        action='store_true',
        help='不生成图表 / Do not generate charts'
    )
    
    parser.add_argument(
        '--dataset',
        type=str,
        help='只汇总指定数据集 / Only summarize specified dataset (e.g., gsm8k)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='静默模式 / Quiet mode'
    )
    
    args = parser.parse_args()
    
    # 创建汇总器 / Create summarizer
    summarizer = ResultSummarizer(
        results_dir=args.results_dir,
        output_dir=args.output_dir,
        verbose=not args.quiet
    )
    
    # 执行汇总 / Execute summarization
    summarizer.summarize_all(
        generate_charts=not args.no_charts,
        dataset_filter=args.dataset
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Summarization interrupted by user.")
        print("⚠️  汇总被用户中断。")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

