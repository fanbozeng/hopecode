"""
Build Vector Embeddings Cache
构建向量嵌入缓存

This script pre-computes embeddings for the knowledge base
to speed up first-time initialization.

此脚本预先计算知识库的嵌入，以加快首次初始化速度。
"""

import time
from pathlib import Path
from engine.vector_retriever import VectorKnowledgeRetriever


def main():
    print("="*80)
    print(" Building Vector Embeddings Cache")
    print(" 构建向量嵌入缓存")
    print("="*80 + "\n")
    
    # Check if knowledge base exists
    kb_path = Path("data/knowledge_base.json")
    if not kb_path.exists():
        print("❌ Error: knowledge_base.json not found in data/")
        print("❌ 错误：data/ 目录中未找到 knowledge_base.json")
        print("\nPlease ensure the knowledge base file exists before running this script.")
        return 1
    
    # Check for local model
    model_path = Path("all-MiniLM-L6-v2")
    if model_path.exists():
        model_name = "all-MiniLM-L6-v2"
        print(f"✓ Found local model at: {model_path}")
        print(f"✓ 找到本地模型: {model_path}")
    else:
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        print(f"⚠ Local model not found, will download from HuggingFace")
        print(f"⚠ 未找到本地模型，将从 HuggingFace 下载")
        print(f"Model: {model_name}\n")
    
    cache_path = Path("data/knowledge_embeddings.pkl")
    
    # Check if cache already exists
    if cache_path.exists():
        print(f"⚠ Cache file already exists: {cache_path}")
        print(f"⚠ 缓存文件已存在: {cache_path}")
        response = input("\nDo you want to rebuild it? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled. Exiting...")
            print("已取消。退出...")
            return 0
        
        # Delete old cache
        cache_path.unlink()
        print("✓ Deleted old cache file")
        print("✓ 已删除旧缓存文件\n")
    
    # Build cache
    print("-"*80)
    print("Starting embedding computation...")
    print("开始计算嵌入...")
    print("-"*80 + "\n")
    
    start_time = time.time()
    
    try:
        # Initialize retriever (will compute and cache embeddings)
        retriever = VectorKnowledgeRetriever(
            knowledge_base_path=str(kb_path),
            model_name=model_name,
            cache_path=str(cache_path),
            use_cache=False  # Force computation
        )
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "="*80)
        print("✅ SUCCESS / 成功")
        print("="*80)
        print(f"\n📊 Statistics:")
        print(f"  - Knowledge entries: {len(retriever.knowledge_entries)}")
        print(f"  - Embedding dimensions: {retriever.embeddings_matrix.shape[1]}")
        print(f"  - Total embeddings: {retriever.embeddings_matrix.shape[0]}")
        print(f"  - Computation time: {elapsed_time:.2f} seconds")
        print(f"  - Cache file: {cache_path}")
        print(f"  - Cache size: {cache_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        print(f"\n📊 统计信息:")
        print(f"  - 知识条目数: {len(retriever.knowledge_entries)}")
        print(f"  - 嵌入维度: {retriever.embeddings_matrix.shape[1]}")
        print(f"  - 总嵌入数: {retriever.embeddings_matrix.shape[0]}")
        print(f"  - 计算时间: {elapsed_time:.2f} 秒")
        print(f"  - 缓存文件: {cache_path}")
        print(f"  - 缓存大小: {cache_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        print("\n" + "="*80)
        print("✓ Cache built successfully! Future initializations will be much faster.")
        print("✓ 缓存构建成功！未来的初始化将更快。")
        print("="*80)
        
        # Test retrieval
        print("\n🔍 Testing retrieval...")
        print("🔍 测试检索...")
        
        test_problem = "An object with mass 10 kg accelerates at 5 m/s²"
        results = retriever.retrieve_with_scores(test_problem, top_k=3, similarity_threshold=0.2)
        
        if results:
            print(f"\n✓ Test successful! Retrieved {len(results)} rules:")
            print(f"✓ 测试成功！检索到 {len(results)} 条规则:")
            for i, (rule, score, category) in enumerate(results, 1):
                cat_str = f"[{category}]" if category else ""
                print(f"  {i}. {cat_str} Score: {score:.3f}")
                print(f"     {rule[:80]}...")
        else:
            print("⚠ Warning: No results found in test query")
            print("⚠ 警告：测试查询未找到结果")
        
        return 0
        
    except Exception as e:
        print("\n" + "="*80)
        print("❌ ERROR / 错误")
        print("="*80)
        print(f"\nFailed to build cache: {e}")
        print(f"构建缓存失败: {e}")
        
        import traceback
        print("\nFull error traceback:")
        print("完整错误跟踪:")
        traceback.print_exc()
        
        return 1


if __name__ == "__main__":
    exit(main())


