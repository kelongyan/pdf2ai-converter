"""Markdown 质量检查模块"""

import re
from typing import Dict, List


class QualityChecker:
    """检查生成的 Markdown 质量"""

    def __init__(self):
        self.issues = []

    def check(self, markdown: str, pdf_pages: int) -> Dict:
        """执行质量检查

        Args:
            markdown: 生成的 Markdown 文本
            pdf_pages: 原始 PDF 页数

        Returns:
            检查结果字典
        """
        self.issues = []
        result = {
            "passed": True,
            "score": 100,
            "issues": [],
            "stats": {},
        }

        # 统计信息
        stats = self._collect_stats(markdown)
        result["stats"] = stats

        # 检查项
        self._check_content_length(markdown, pdf_pages)
        self._check_structure(markdown)
        self._check_formulas(markdown)
        self._check_tables(markdown)
        self._check_encoding(markdown)

        # 计算得分
        result["issues"] = self.issues
        result["score"] = max(0, 100 - len(self.issues) * 5)
        result["passed"] = result["score"] >= 60

        return result

    def _collect_stats(self, markdown: str) -> Dict:
        """收集统计信息"""
        lines = markdown.split("\n")
        return {
            "total_lines": len(lines),
            "total_chars": len(markdown),
            "headers": len(re.findall(r"^#{1,6}\s+.+", markdown, re.MULTILINE)),
            "formulas": len(re.findall(r"\$.*?\$", markdown)),
            "tables": len(re.findall(r"\|.*\|", markdown)),
            "code_blocks": len(re.findall(r"```", markdown)) // 2,
            "lists": len(re.findall(r"^[\-\*\+]\s+", markdown, re.MULTILINE)),
        }

    def _check_content_length(self, markdown: str, pdf_pages: int):
        """检查内容长度是否合理"""
        lines = len(markdown.split("\n"))
        expected_min = pdf_pages * 20  # 每页至少 20 行

        if lines < expected_min:
            self.issues.append(
                f"内容过短：{lines} 行（预期至少 {expected_min} 行）"
            )

    def _check_structure(self, markdown: str):
        """检查文档结构"""
        # 检查是否有标题
        headers = re.findall(r"^#{1,6}\s+.+", markdown, re.MULTILINE)
        if len(headers) == 0:
            self.issues.append("缺少标题结构")

        # 检查是否有过多的分隔符（可能是转换失败）
        separators = re.findall(r"^---+$", markdown, re.MULTILINE)
        if len(separators) > 20:
            self.issues.append(f"分隔符过多：{len(separators)} 个（可能是页面分隔）")

    def _check_formulas(self, markdown: str):
        """检查公式格式"""
        # 检查未闭合的公式
        single_dollars = re.findall(r"\$", markdown)
        if len(single_dollars) % 2 != 0:
            self.issues.append("公式符号未配对（$ 数量为奇数）")

        # 检查双美元符号
        double_dollars = re.findall(r"\$\$", markdown)
        if len(double_dollars) % 2 != 0:
            self.issues.append("块级公式符号未配对（$$ 数量为奇数）")

    def _check_tables(self, markdown: str):
        """检查表格格式"""
        # 查找表格
        table_lines = re.findall(r"\|.*\|", markdown)
        if len(table_lines) > 0:
            # 检查表格分隔符
            separator_lines = [
                line for line in table_lines if re.match(r"\|[\s\-:]+\|", line)
            ]
            if len(separator_lines) == 0:
                self.issues.append("表格缺少分隔符行")

    def _check_encoding(self, markdown: str):
        """检查编码问题"""
        # 检查常见的乱码模式
        if "�" in markdown:
            self.issues.append("检测到乱码字符（�）")

        # 检查是否有大量重复的错误信息
        error_patterns = [
            "抱歉，我无法",
            "I cannot",
            "I can't see",
            "无法看到",
        ]
        for pattern in error_patterns:
            count = markdown.count(pattern)
            if count > 2:
                self.issues.append(f"检测到模型错误响应（'{pattern}' 出现 {count} 次）")

    def print_report(self, result: Dict):
        """打印检查报告"""
        print("\n" + "=" * 60)
        print("📊 质量检查报告")
        print("=" * 60)

        # 统计信息
        stats = result["stats"]
        print(f"\n📈 统计信息：")
        print(f"  总行数：{stats['total_lines']}")
        print(f"  总字符：{stats['total_chars']}")
        print(f"  标题数：{stats['headers']}")
        print(f"  公式数：{stats['formulas']}")
        print(f"  表格数：{stats['tables']}")
        print(f"  代码块：{stats['code_blocks']}")
        print(f"  列表项：{stats['lists']}")

        # 得分
        score = result["score"]
        print(f"\n🎯 质量得分：{score}/100")

        # 问题列表
        if result["issues"]:
            print(f"\n⚠️  发现 {len(result['issues'])} 个问题：")
            for i, issue in enumerate(result["issues"], 1):
                print(f"  {i}. {issue}")
        else:
            print("\n✅ 未发现问题")

        # 结论
        print(f"\n{'✅ 通过' if result['passed'] else '❌ 未通过'}")
        print("=" * 60 + "\n")
