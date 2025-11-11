"""
评估工具测试脚本
Evaluation Tools Test Script

用于测试批量CF/AC评估工具和统计汇总工具是否正常工作
Tests if batch CF/AC evaluation tool and result summarization tool work correctly
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """测试导入 / Test imports"""
    print("="*80)
    print("🧪 测试1: 检查模块导入 / Test 1: Check Module Imports")
    print("="*80)
    
    try:
        from comparasion.evaluate_cf_ac_batch import CFACBatchEvaluator
        print("✅ evaluate_cf_ac_batch.py 导入成功")
    except Exception as e:
        print(f"❌ evaluate_cf_ac_batch.py 导入失败: {e}")
        return False
    
    try:
        from comparasion.summarize_results import ResultSummarizer
        print("✅ summarize_results.py 导入成功")
    except Exception as e:
        print(f"❌ summarize_results.py 导入失败: {e}")
        return False
    
    try:
        from causal_evaluation import (
            CausalInterventionEvaluator,
            AbductiveReasoningEvaluator,
            RewardEvaluator
        )
        print("✅ causal_evaluation.py 导入成功")
    except Exception as e:
        print(f"❌ causal_evaluation.py 导入失败: {e}")
        return False
    
    print("\n✅ 所有模块导入成功！\n")
    return True


def test_directory_structure():
    """测试目录结构 / Test directory structure"""
    print("="*80)
    print("🧪 测试2: 检查目录结构 / Test 2: Check Directory Structure")
    print("="*80)
    
    results_dir = Path("comparasion/results")
    
    if not results_dir.exists():
        print(f"⚠️  结果目录不存在: {results_dir}")
        print(f"⚠️  Results directory does not exist: {results_dir}")
        print("💡 请先运行实验生成结果文件")
        print("💡 Please run experiments first to generate result files")
        return False
    
    print(f"✅ 结果目录存在: {results_dir}")
    
    # 检查是否有结果文件
    json_files = list(results_dir.rglob("*.json"))
    
    if not json_files:
        print(f"⚠️  未找到结果文件")
        print(f"⚠️  No result files found")
        print("💡 请先运行实验生成结果文件")
        print("💡 Please run experiments first to generate result files")
        return False
    
    print(f"✅ 找到 {len(json_files)} 个结果文件")
    
    # 列出前5个文件
    print("\n📄 示例文件 / Sample files:")
    for i, file in enumerate(json_files[:5], 1):
        print(f"  {i}. {file.relative_to(results_dir.parent)}")
    
    if len(json_files) > 5:
        print(f"  ... 还有 {len(json_files) - 5} 个文件")
    
    print()
    return True


def test_result_file_format():
    """测试结果文件格式 / Test result file format"""
    print("="*80)
    print("🧪 测试3: 检查结果文件格式 / Test 3: Check Result File Format")
    print("="*80)
    
    results_dir = Path("comparasion/results")
    json_files = list(results_dir.rglob("*.json"))
    
    if not json_files:
        print("⚠️  没有结果文件可测试")
        return False
    
    # 测试第一个文件
    test_file = json_files[0]
    print(f"📄 测试文件: {test_file.name}")
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ JSON格式正确")
        
        # 检查必需字段
        required_fields = ['method', 'dataset', 'results', 'statistics']
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            print(f"⚠️  缺少字段: {missing_fields}")
        else:
            print("✅ 包含所有必需字段")
        
        # 检查是否有CF/AC分数
        stats = data.get('statistics', {})
        has_cf = 'cf_score' in stats
        has_ac = 'ac_score' in stats
        
        if has_cf and has_ac:
            print(f"✅ 已包含CF/AC分数 (CF={stats['cf_score']:.3f}, AC={stats['ac_score']:.3f})")
        else:
            print("⚠️  尚未评估CF/AC分数")
            print("💡 运行: python comparasion/evaluate_cf_ac_batch.py")
        
        # 检查results数组
        results = data.get('results', [])
        print(f"✅ 包含 {len(results)} 个问题结果")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False


def test_evaluator_initialization():
    """测试评估器初始化 / Test evaluator initialization"""
    print("="*80)
    print("🧪 测试4: 测试评估器初始化 / Test 4: Test Evaluator Initialization")
    print("="*80)
    
    try:
        from comparasion.evaluate_cf_ac_batch import CFACBatchEvaluator
        
        print("🔧 初始化CFACBatchEvaluator...")
        evaluator = CFACBatchEvaluator(
            results_dir="comparasion/results",
            verbose=False
        )
        print("✅ CFACBatchEvaluator 初始化成功")
        
    except Exception as e:
        print(f"❌ CFACBatchEvaluator 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        from comparasion.summarize_results import ResultSummarizer
        
        print("🔧 初始化ResultSummarizer...")
        summarizer = ResultSummarizer(
            results_dir="comparasion/results",
            output_dir="comparasion/summary_test",
            verbose=False
        )
        print("✅ ResultSummarizer 初始化成功")
        
    except Exception as e:
        print(f"❌ ResultSummarizer 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ 所有评估器初始化成功！\n")
    return True


def test_causal_evaluation_modules():
    """测试因果评估模块 / Test causal evaluation modules"""
    print("="*80)
    print("🧪 测试5: 测试因果评估模块 / Test 5: Test Causal Evaluation Modules")
    print("="*80)
    
    try:
        from causal_evaluation import (
            CausalInterventionEvaluator,
            AbductiveReasoningEvaluator,
            RewardEvaluator
        )
        
        print("🔧 初始化CausalInterventionEvaluator...")
        causal_eval = CausalInterventionEvaluator(verbose=False)
        print("✅ CausalInterventionEvaluator 初始化成功")
        
        print("🔧 初始化AbductiveReasoningEvaluator...")
        abductive_eval = AbductiveReasoningEvaluator(verbose=False)
        print("✅ AbductiveReasoningEvaluator 初始化成功")
        
        print("🔧 初始化RewardEvaluator...")
        reward_eval = RewardEvaluator(verbose=False)
        print("✅ RewardEvaluator 初始化成功")
        
        print("\n✅ 所有因果评估模块初始化成功！\n")
        return True
        
    except Exception as e:
        print(f"❌ 因果评估模块初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """打印测试总结 / Print test summary"""
    print("="*80)
    print("📊 测试总结 / Test Summary")
    print("="*80)
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {failed}/{total}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！评估工具已准备就绪！")
        print("🎉 All tests passed! Evaluation tools are ready!")
        print("\n💡 下一步:")
        print("   1. 运行: python comparasion/evaluate_cf_ac_batch.py")
        print("   2. 运行: python comparasion/summarize_results.py")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")
        print("⚠️  Some tests failed, please check error messages")
    
    print("="*80)


def main():
    """主测试函数 / Main test function"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "评估工具测试脚本" + " "*20 + "                  ║")
    print("║" + " "*15 + "Evaluation Tools Test Script" + " "*15 + "           ║")
    print("╚" + "="*78 + "╝")
    print("\n")
    
    results = {}
    
    # 运行测试
    results['test_imports'] = test_imports()
    results['test_directory_structure'] = test_directory_structure()
    results['test_result_file_format'] = test_result_file_format()
    results['test_evaluator_initialization'] = test_evaluator_initialization()
    results['test_causal_evaluation_modules'] = test_causal_evaluation_modules()
    
    # 打印总结
    print_summary(results)
    
    # 返回退出码
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

