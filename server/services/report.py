from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.db.models import ReportRequest, User, UserDeviceReport
from server.llm.factory import model_manager
from server.schemas.common import AuthContext


class ReportService:
    def resolve_target_user(
        self,
        db: Session,
        auth_context: AuthContext,
        target_account_code: str | None,
    ) -> User:
        if target_account_code and target_account_code != auth_context.account_code:
            if "report:read:any" not in auth_context.permissions:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to read other reports")
            user = db.scalar(select(User).where(User.account_code == target_account_code))
            if user is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")
            return user

        user = db.scalar(select(User).where(User.id == auth_context.user_id))
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def fetch_report(self, db: Session, auth_context: AuthContext, month: str, target_account_code: str | None = None) -> tuple[User, UserDeviceReport]:
        target_user = self.resolve_target_user(db, auth_context, target_account_code)
        report = db.scalar(
            select(UserDeviceReport).where(
                UserDeviceReport.user_id == target_user.id,
                UserDeviceReport.month == month,
            )
        )
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No report found for the requested month")
        db.add(
            ReportRequest(
                requester_user_id=auth_context.user_id,
                target_user_id=target_user.id,
                month=month,
                status="completed",
            )
        )
        db.commit()
        return target_user, report

    def generate_report_markdown(self, user: User, report: UserDeviceReport) -> str:
        prompt = f"""请基于以下结构化信息生成中文 Markdown 报告，不要编造不存在的数据。
标题固定为《扫地机器人使用情况报告与保养建议》。
用户：{user.full_name}
账号：{user.account_code}
月份：{report.month}
功能特征：{report.feature}
清洁效率：{report.efficiency}
耗材状态：{report.consumables}
对比分析：{report.comparison}
"""
        rendered = model_manager.invoke_chat(prompt)
        if rendered:
            return rendered.strip()

        return (
            "# 扫地机器人使用情况报告与保养建议\n\n"
            f"- 用户：{user.full_name}（账号 {user.account_code}）\n"
            f"- 月份：{report.month}\n\n"
            "## 本月摘要\n\n"
            f"- 功能特征：{report.feature}\n"
            f"- 清洁效率：{report.efficiency}\n"
            f"- 耗材状态：{report.consumables}\n"
            f"- 对比分析：{report.comparison}\n\n"
            "## 建议\n\n"
            "- 优先根据耗材状态安排滤网、滚刷和边刷检查。\n"
            "- 若清洁效率下降，优先检查地面障碍物、集尘盒和地图状态。\n"
            "- 保留固定清洁频率，避免长期积灰导致效率波动。\n"
        )

    def latest_month_for_user(self, db: Session, user_id: UUID) -> str | None:
        rows = db.scalars(
            select(UserDeviceReport.month).where(UserDeviceReport.user_id == user_id).order_by(UserDeviceReport.month.desc())
        ).all()
        return rows[0] if rows else None


report_service = ReportService()
