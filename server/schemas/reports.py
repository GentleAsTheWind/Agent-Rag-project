from pydantic import BaseModel


class ReportQueryRequest(BaseModel):
    month: str | None = None
    target_account_code: str | None = None


class ReportQueryResponse(BaseModel):
    report_markdown: str
    month: str
    target_account_code: str
