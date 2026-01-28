#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一性能测试脚本

说明：
- 这里只给出 **示例实现**，你可以根据需要补充逻辑、数据路径和指标统计方式
- 默认假设在项目根目录执行：`python -m test.performance.run_performance_tests`
"""

import os
import sys
import time
from typing import Dict, Any


def project_root() -> str:
    """返回项目根目录路径"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def setup_pythonpath() -> None:
    """确保可以导入 backend 模块"""
    root = project_root()
    if root not in sys.path:
        sys.path.insert(0, root)


setup_pythonpath()


def time_function(func, *args, repeat: int = 3, **kwargs) -> Dict[str, Any]:
    """
    简单的计时工具：多次运行取平均

    返回:
        {
            "runs": repeat,
            "total_time": float,
            "avg_time": float,
        }
    """
    start = time.perf_counter()
    for _ in range(repeat):
        func(*args, **kwargs)
    end = time.perf_counter()
    total = end - start
    return {
        "runs": repeat,
        "total_time": total,
        "avg_time": total / repeat if repeat > 0 else 0.0,
    }


def test_keyword_extractor() -> Dict[str, Any]:
    """
    示例：对 keyword_extractor 进行简单性能测试
    TODO:
    - 根据你的实际情况指定测试数据目录，例如 data/perf_samples/keywords/
    - 控制文档数 / 文本大小等
    """
    from backend.core import keyword_extractor as ke

    # 示例：从 data/uploads 或自定义目录读取少量 txt 文件
    sample_dir = os.path.join(project_root(), "data", "uploads")

    docs = []
    for root, _, files in os.walk(sample_dir):
        for fname in files:
            if fname.lower().endswith(".txt"):
                fpath = os.path.join(root, fname)
                try:
                    docs.append(ke.read_file(fpath))
                except Exception:
                    continue
            if len(docs) >= 10:  # 简单限制样本数，后续可调整
                break
        if len(docs) >= 10:
            break

    if not docs:
        return {
            "module": "keyword_extractor",
            "status": "no_data",
            "detail": "未找到测试用 txt 文件，请在 data/uploads 或自定义目录放入样本。",
        }

    def _run_extract():
        # 示例：简单地对所有文本进行 clean + TF-IDF 拟合
        cleaned = [ke.basic_clean(t) for t in docs]
        # 这里只是演示，不调用内部所有函数，你可以根据需要改成完整流程
        from sklearn.feature_extraction.text import TfidfVectorizer

        vec = TfidfVectorizer(max_features=5000)
        _ = vec.fit_transform(cleaned)

    stats = time_function(_run_extract, repeat=3)
    return {
        "module": "keyword_extractor",
        "status": "ok",
        "num_docs": len(docs),
        **stats,
    }


def test_recommender() -> Dict[str, Any]:
    """
    示例：对 recommender 进行简单性能测试
    TODO:
    - 提供一批伪造/真实的资源字典列表
    - 控制候选资源数量和用户文档数量
    """
    from backend.core import recommender as rec

    # 简单构造一些假数据作为示例
    user_docs = [
        "This is a short example document about machine learning and neural networks."
    ] * 5  # 5 个用户文档

    resources = [
        {
            "title": f"Resource {i}",
            "content": f"This is resource {i} about deep learning and transformers.",
        }
        for i in range(100)
    ]

    def _run_recommend():
        _ = rec.recommend_best_resources(
            user_docs=user_docs,
            resources=resources,
            top_k=10,
        )

    stats = time_function(_run_recommend, repeat=5)
    return {
        "module": "recommender",
        "status": "ok",
        "num_user_docs": len(user_docs),
        "num_resources": len(resources),
        **stats,
    }


def main():
    print("=== 性能测试开始 ===")
    results = []

    # 你可以按需启用/关闭某些测试
    tests = [
        ("keyword_extractor", test_keyword_extractor),
        ("recommender", test_recommender),
        # TODO: 后续可添加 resource_searcher / ai_summarizer 的性能测试
    ]

    for name, fn in tests:
        print(f"\n--- 运行模块：{name} ---")
        try:
            res = fn()
            results.append(res)
            print(res)
        except Exception as e:
            print(f"[ERROR] {name} 测试失败：{e}")
            results.append(
                {"module": name, "status": "error", "error": str(e)}
            )

    print("\n=== 性能测试结束 ===")
    print("汇总结果：")
    for r in results:
        print(r)


if __name__ == "__main__":
    main()

