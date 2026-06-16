"""意图识别服务。

当前版本先用规则分类，目的是把业务链路跑通。
后续可以替换成“大模型分类 + 结构化输出”。
"""

import re

from server.schemas.common import IntentResult


RISK_PATTERNS = ("忽略之前", "system prompt", "越权", "管理员权限", "导出所有用户", "绕过权限")
REPORT_PATTERNS = ("报告", "使用记录", "使用情况", "月报", "查询记录")
TROUBLE_PATTERNS = ("故障", "报错", "迷路", "卡住", "撞", "回充失败", "不工作", "异常")
MAINTENANCE_PATTERNS = ("保养", "维护", "清洁", "清理", "耗材", "滤网", "滚刷")
PURCHASE_PATTERNS = ("选购", "推荐", "值得买吗", "买哪种", "户型", "预算", "适合")
PRODUCT_PATTERNS = ("扫地机器人", "扫拖", "机器人", "拖地", "吸力", "避障")


class IntentService:
    """把用户输入归类为可路由的业务意图。"""

    month_pattern = re.compile(r"(20\d{2})[-年/.](0?[1-9]|1[0-2])")
    account_pattern = re.compile(r"\b(10\d{2}|20\d{2}|30\d{2}|40\d{2}|50\d{2}|90\d{2})\b")

    def classify(self, message: str, client_context: dict | None = None) -> IntentResult:
        """返回结构化意图结果。

        除了 intent，还会抽取：
        - month
        - target_account_code
        - risk_level
        """
        text = message.strip()
        lowered = text.lower()
        client_context = client_context or {}

        risk_level = "high" if any(pattern in lowered or pattern in text for pattern in RISK_PATTERNS) else "low"
        target_account_code = client_context.get("target_account_code") or self._extract_account_code(text)
        resolved_month = self._extract_month(text) or client_context.get("month")

        if any(keyword in text for keyword in REPORT_PATTERNS):
            required = [] if resolved_month else ["month"]
            return IntentResult(
                intent="personal_report",
                confidence=0.96,
                required_entities=required,
                needs_auth=True,
                risk_level=risk_level,
                resolved_month=resolved_month,
                target_account_code=target_account_code,
            )

        if any(keyword in text for keyword in TROUBLE_PATTERNS):
            return IntentResult(intent="troubleshooting", confidence=0.91, risk_level=risk_level)

        if any(keyword in text for keyword in MAINTENANCE_PATTERNS):
            return IntentResult(intent="maintenance", confidence=0.9, risk_level=risk_level)

        if any(keyword in text for keyword in PURCHASE_PATTERNS):
            return IntentResult(intent="purchase_advice", confidence=0.88, risk_level=risk_level)

        if any(keyword in text for keyword in PRODUCT_PATTERNS):
            return IntentResult(intent="product_qa", confidence=0.82, risk_level=risk_level)

        return IntentResult(intent="unknown", confidence=0.35, risk_level=risk_level)

    def _extract_month(self, text: str) -> str | None:
        """从自然语言里提取 YYYY-MM。"""
        match = self.month_pattern.search(text)
        if not match:
            return None
        year, month = match.groups()
        return f"{year}-{int(month):02d}"

    def _extract_account_code(self, text: str) -> str | None:
        """从文本里提取业务账号。"""
        match = self.account_pattern.search(text)
        return match.group(1) if match else None


intent_service = IntentService()
