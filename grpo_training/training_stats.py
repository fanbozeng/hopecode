"""
训练统计模块
用于追踪和可视化GRPO训练过程中的正确率变化
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np


class TrainingStats:
    """训练统计类"""

    def __init__(self, component_name: str, stats_dir: str = "training_stats"):
        """
        初始化统计器

        Args:
            component_name: 组件名称（如generator_1, critic等）
            stats_dir: 统计数据保存目录
        """
        self.component_name = component_name
        self.stats_dir = Path(stats_dir)
        self.stats_dir.mkdir(exist_ok=True)

        # 统计文件路径
        self.stats_file = self.stats_dir / f"{component_name}_stats.json"

        # 加载已有统计数据
        self.stats_data = self._load_stats()

    def _load_stats(self) -> Dict[str, Any]:
        """加载已有统计数据"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        # 返回默认结构
        return {
            "component_name": self.component_name,
            "start_time": datetime.now().isoformat(),
            "epochs": [],
            "latest_epoch": 0
        }

    def save_stats(self):
        """保存统计数据"""
        self.stats_data["last_updated"] = datetime.now().isoformat()
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats_data, f, indent=2, ensure_ascii=False)

    def record_epoch(
        self,
        epoch_num: int,
        total_problems: int,
        correct_answers: int,
        total_reward: float,
        avg_reward: float,
        additional_metrics: Optional[Dict[str, Any]] = None
    ):
        """
        记录一个epoch的统计数据

        Args:
            epoch_num: epoch编号
            total_problems: 总题目数
            correct_answers: 正确答案数
            total_reward: 总奖励分数
            avg_reward: 平均奖励分数
            additional_metrics: 额外指标
        """
        accuracy = correct_answers / total_problems if total_problems > 0 else 0.0

        epoch_data = {
            "epoch": epoch_num,
            "timestamp": datetime.now().isoformat(),
            "total_problems": total_problems,
            "correct_answers": correct_answers,
            "accuracy": accuracy,
            "total_reward": total_reward,
            "avg_reward": avg_reward
        }

        # 添加额外指标
        if additional_metrics:
            epoch_data.update(additional_metrics)

        # 更新或添加epoch数据
        existing_epoch_idx = None
        for i, epoch in enumerate(self.stats_data["epochs"]):
            if epoch["epoch"] == epoch_num:
                existing_epoch_idx = i
                break

        if existing_epoch_idx is not None:
            self.stats_data["epochs"][existing_epoch_idx] = epoch_data
        else:
            self.stats_data["epochs"].append(epoch_data)

        # 更新最新epoch
        self.stats_data["latest_epoch"] = max(self.stats_data["latest_epoch"], epoch_num)

        # 按epoch排序
        self.stats_data["epochs"].sort(key=lambda x: x["epoch"])

        # 保存数据
        self.save_stats()

        # 打印统计信息
        print(f"\n=== {self.component_name} Epoch {epoch_num} 统计 ===")
        print(f"总题目数: {total_problems}")
        print(f"正确答案数: {correct_answers}")
        print(f"正确率: {accuracy:.3f} ({accuracy*100:.1f}%)")
        print(f"平均奖励: {avg_reward:.3f}")

        return epoch_data

    def get_accuracy_trend(self) -> List[float]:
        """获取正确率趋势"""
        return [epoch["accuracy"] for epoch in self.stats_data["epochs"]]

    def get_reward_trend(self) -> List[float]:
        """获取平均奖励趋势"""
        return [epoch["avg_reward"] for epoch in self.stats_data["epochs"]]

    def get_latest_accuracy(self) -> float:
        """获取最新正确率"""
        if not self.stats_data["epochs"]:
            return 0.0
        return self.stats_data["epochs"][-1]["accuracy"]

    def get_best_epoch(self) -> Dict[str, Any]:
        """获取表现最好的epoch"""
        if not self.stats_data["epochs"]:
            return {}

        best_epoch = max(self.stats_data["epochs"], key=lambda x: x["accuracy"])
        return best_epoch

    def print_summary(self):
        """打印统计摘要"""
        if not self.stats_data["epochs"]:
            print(f"{self.component_name}: 暂无统计数据")
            return

        epochs = self.stats_data["epochs"]
        latest = epochs[-1]
        best = self.get_best_epoch()

        print(f"\n=== {self.component_name} 训练统计摘要 ===")
        print(f"总训练轮次: {len(epochs)}")
        print(f"最新正确率: {latest['accuracy']:.3f} ({latest['accuracy']*100:.1f}%)")
        print(f"最佳正确率: {best['accuracy']:.3f} ({best['accuracy']*100:.1f}%) - Epoch {best['epoch']}")
        print(f"最新平均奖励: {latest['avg_reward']:.3f}")

        # 计算改进趋势
        if len(epochs) >= 2:
            recent_5 = epochs[-5:] if len(epochs) >= 5 else epochs
            acc_trend = self.get_accuracy_trend()[-5:] if len(epochs) >= 5 else self.get_accuracy_trend()

            if len(acc_trend) >= 2:
                improvement = acc_trend[-1] - acc_trend[0]
                print(f"最近{len(recent_5)}轮改进: {improvement:+.3f} ({improvement*100:+.1f}%)")

    def plot_progress(self, save_path: Optional[str] = None):
        """
        绘制训练进度图表

        Args:
            save_path: 保存路径，如果为None则显示图表
        """
        if not self.stats_data["epochs"]:
            print(f"{self.component_name}: 暂无数据可绘制")
            return

        epochs = [epoch["epoch"] for epoch in self.stats_data["epochs"]]
        accuracies = [epoch["accuracy"] for epoch in self.stats_data["epochs"]]
        avg_rewards = [epoch["avg_reward"] for epoch in self.stats_data["epochs"]]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        # 正确率趋势
        ax1.plot(epochs, accuracies, 'b-o', linewidth=2, markersize=6)
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Accuracy')
        ax1.set_title(f'{self.component_name} 正确率趋势')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 1)

        # 添加数值标签
        for i, (epoch, acc) in enumerate(zip(epochs, accuracies)):
            ax1.annotate(f'{acc:.3f}', (epoch, acc), textcoords="offset points",
                        xytext=(0,10), ha='center', fontsize=8)

        # 平均奖励趋势
        ax2.plot(epochs, avg_rewards, 'r-s', linewidth=2, markersize=6)
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Average Reward')
        ax2.set_title(f'{self.component_name} 平均奖励趋势')
        ax2.grid(True, alpha=0.3)

        # 添加数值标签
        for i, (epoch, reward) in enumerate(zip(epochs, avg_rewards)):
            ax2.annotate(f'{reward:.3f}', (epoch, reward), textcoords="offset points",
                        xytext=(0,10), ha='center', fontsize=8)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图表已保存到: {save_path}")
        else:
            plt.show()

        plt.close()

    def export_detailed_report(self, output_path: Optional[str] = None) -> str:
        """
        导出详细的训练报告

        Args:
            output_path: 输出路径，如果为None则使用默认路径

        Returns:
            报告文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.stats_dir / f"{self.component_name}_report_{timestamp}.txt"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"=== {self.component_name} 训练报告 ===\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            if not self.stats_data["epochs"]:
                f.write("暂无训练数据\n")
                return str(output_path)

            # 基本信息
            f.write(f"训练开始时间: {self.stats_data.get('start_time', 'N/A')}\n")
            f.write(f"总训练轮次: {len(self.stats_data['epochs'])}\n")
            f.write(f"最新更新: {self.stats_data.get('last_updated', 'N/A')}\n\n")

            # 详细统计
            epochs = self.stats_data["epochs"]
            latest = epochs[-1]
            best = self.get_best_epoch()

            f.write("=== 性能摘要 ===\n")
            f.write(f"最新正确率: {latest['accuracy']:.4f} ({latest['accuracy']*100:.2f}%)\n")
            f.write(f"最佳正确率: {best['accuracy']:.4f} ({best['accuracy']*100:.2f}%) - Epoch {best['epoch']}\n")
            f.write(f"最新平均奖励: {latest['avg_reward']:.4f}\n")
            f.write(f"最佳平均奖励: {max(e['avg_reward'] for e in epochs):.4f}\n\n")

            # Epoch详情
            f.write("=== Epoch 详细数据 ===\n")
            f.write(f"{'Epoch':<6} {'题目数':<8} {'正确数':<8} {'正确率':<10} {'平均奖励':<10} {'时间':<20}\n")
            f.write("-" * 70 + "\n")

            for epoch in epochs:
                timestamp = datetime.fromisoformat(epoch['timestamp']).strftime('%m-%d %H:%M')
                f.write(f"{epoch['epoch']:<6} {epoch['total_problems']:<8} "
                       f"{epoch['correct_answers']:<8} {epoch['accuracy']:<10.4f} "
                       f"{epoch['avg_reward']:<10.4f} {timestamp:<20}\n")

        print(f"详细报告已导出到: {output_path}")
        return str(output_path)


def compare_components(components: List[str], stats_dir: str = "training_stats") -> Dict[str, Any]:
    """
    比较多个组件的训练统计

    Args:
        components: 组件名称列表
        stats_dir: 统计数据目录

    Returns:
        比较结果
    """
    comparison = {
        "components": components,
        "stats": {},
        "summary": {}
    }

    # 加载各组件统计
    for component in components:
        stats = TrainingStats(component, stats_dir)
        if stats.stats_data["epochs"]:
            comparison["stats"][component] = {
                "latest_accuracy": stats.get_latest_accuracy(),
                "best_epoch": stats.get_best_epoch(),
                "total_epochs": len(stats.stats_data["epochs"]),
                "accuracy_trend": stats.get_accuracy_trend()
            }

    # 生成比较摘要
    if comparison["stats"]:
        # 找出表现最好的组件
        best_component = max(comparison["stats"].items(),
                           key=lambda x: x[1]["latest_accuracy"])

        comparison["summary"] = {
            "best_component": best_component[0],
            "best_accuracy": best_component[1]["latest_accuracy"],
            "component_count": len(comparison["stats"]),
            "comparison_time": datetime.now().isoformat()
        }

    return comparison


def plot_multiple_components(components: List[str], stats_dir: str = "training_stats",
                           save_path: Optional[str] = None):
    """
    绘制多个组件的正确率对比图

    Args:
        components: 组件名称列表
        stats_dir: 统计数据目录
        save_path: 保存路径
    """
    plt.figure(figsize=(12, 8))

    for component in components:
        stats = TrainingStats(component, stats_dir)
        if stats.stats_data["epochs"]:
            epochs = [epoch["epoch"] for epoch in stats.stats_data["epochs"]]
            accuracies = [epoch["accuracy"] for epoch in stats.stats_data["epochs"]]
            plt.plot(epochs, accuracies, 'o-', linewidth=2, markersize=6,
                    label=f'{component} (最新: {stats.get_latest_accuracy():.3f})')

    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.title('各组件正确率趋势对比')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 1)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"对比图表已保存到: {save_path}")
    else:
        plt.show()

    plt.close()