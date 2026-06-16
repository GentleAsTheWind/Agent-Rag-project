"""报告查询 API。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.api.deps import get_current_auth_context
from server.db.session import get_db
from server.schemas.common import AuthContext
from server.schemas.reports import ReportQueryRequest, ReportQueryResponse
from server.services.report import report_service


router = APIRouter(tags=["reports"])


@router.post("/reports/query", response_model=ReportQueryResponse)
def query_report(
    payload: ReportQueryRequest,
    auth_context: AuthContext = Depends(get_current_auth_context),
    db: Session = Depends(get_db),
) -> ReportQueryResponse:
    """直接查结构化报告，不经过通用 chat 路由。"""
    month = payload.month or report_service.latest_month_for_user(db, auth_context.user_id)
    if month is None:
        return ReportQueryResponse(report_markdown="未找到任何可用报告。", month="unknown", target_account_code=payload.target_account_code or auth_context.account_code or "")
    target_user, report = report_service.fetch_report(db, auth_context, month, payload.target_account_code)
    markdown = report_service.generate_report_markdown(target_user, report)
    return ReportQueryResponse(
        report_markdown=markdown,
        month=month,
        target_account_code=target_user.account_code or "",
    )
