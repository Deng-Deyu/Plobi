"""
研究员 Agent 实现
Phase 3: 网络检索、信息整理

使用 DuckDuckGo 搜索（无需 API Key），支持 MCP 搜索工具作为补充。
"""

import asyncio
from typing import Optional
from .base_agent import BaseAgent


class ResearcherAgent(BaseAgent):
    """研究员：新技术/新消息收集、网络检索、信息整理"""

    def _build_system_prompt(self) -> str:
        return f"""你是研究员，负责新技术/新消息收集、网络检索、信息整理。

你的职责：
1. 收集关于指定主题的最新资料
2. 整理成结构化报告
3. 提供数据来源和引用

你的工作流程：
1. 分析任务需求，提取关键搜索词
2. 使用搜索工具收集相关信息
3. 筛选、验证信息来源
4. 整理成结构化报告

你的风格：
- 严谨、数据驱动
- 注重事实准确性
- 提供清晰的结论

输出格式：
## 研究摘要
{{简要总结}}

## 关键发现
- {{发现1}}
- {{发现2}}

## 数据来源
- {{来源1}}
- {{来源2}}

## 详细报告
{{详细内容}}
"""

    async def execute(
        self,
        task_description: str,
        input_data: Optional[str] = None,
        memory_context: str = ""
    ) -> str:
        """执行任务：先搜索，再让 LLM 整理报告"""
        # 提取搜索关键词（简单策略：取任务描述的前30个词）
        search_query = self._extract_search_query(task_description)

        # 执行搜索
        search_results = await self._search(search_query)

        # 构建增强的输入
        enriched_input = f"""任务描述：{task_description}

输入数据：{input_data or '无'}

网络搜索结果：
{search_results}

请基于以上搜索结果，整理出一份结构化的研究报告。
"""

        # 调用基类的 execute，传入增强后的输入
        return await super().execute(
            task_description=task_description,
            input_data=enriched_input,
            memory_context=memory_context
        )

    def _extract_search_query(self, task_description: str) -> str:
        """从任务描述中提取搜索关键词"""
        # 简单策略：取前 50 个字符作为搜索词
        # 后续可以交给 LLM 来优化
        query = task_description.strip()
        if len(query) > 100:
            query = query[:100]
        return query

    async def _search(self, query: str) -> str:
        """使用 DuckDuckGo 搜索"""
        try:
            from duckduckgo_search import DDGS
            results_text = []
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=5)
                for i, r in enumerate(results, 1):
                    title = r.get("title", "")
                    href = r.get("href", "")
                    body = r.get("body", "")
                    results_text.append(f"[{i}] {title}\n链接: {href}\n摘要: {body}\n")
            return "\n".join(results_text) if results_text else "未找到相关搜索结果。"
        except Exception as e:
            return f"搜索过程中出现错误: {e}\n请确保已安装 duckduckgo-search 库。"
