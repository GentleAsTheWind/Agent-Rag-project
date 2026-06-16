from datetime import datetime

from fastapi import HTTPException
from langgraph.graph import END, START, StateGraph

from server.graph.state import WorkflowState
from server.schemas.common import Citation
from server.services.audit import audit_service
from server.services.intent import intent_service
from server.services.rag import rag_service
from server.services.report import report_service


FAQ_INTENTS = {"product_qa", "troubleshooting", "maintenance", "purchase_advice"}


class WorkflowEngine:
    def __init__(self) -> None:
        graph = StateGraph(WorkflowState)
        graph.add_node("intent_classifier", self.intent_classifier)
        graph.add_node("policy_guard", self.policy_guard)
        graph.add_node("faq_rag", self.faq_rag)
        graph.add_node("report_fetch", self.report_fetch)
        graph.add_node("report_generate", self.report_generate)
        graph.add_node("fallback", self.fallback)
        graph.add_node("handoff", self.handoff)

        graph.add_edge(START, "intent_classifier")
        graph.add_conditional_edges(
            "intent_classifier",
            self.route_from_intent,
            {
                "policy_guard": "policy_guard",
                "fallback": "fallback",
                "handoff": "handoff",
            },
        )
        graph.add_conditional_edges(
            "policy_guard",
            self.route_after_policy,
            {
                "faq_rag": "faq_rag",
                "report_fetch": "report_fetch",
                "handoff": "handoff",
            },
        )
        graph.add_edge("report_fetch", "report_generate")
        graph.add_edge("faq_rag", END)
        graph.add_edge("report_generate", END)
        graph.add_edge("fallback", END)
        graph.add_edge("handoff", END)
        self.app = graph.compile()

    def invoke(self, state: WorkflowState) -> WorkflowState:
        return self.app.invoke(state)

    def intent_classifier(self, state: WorkflowState) -> WorkflowState:
        result = intent_service.classify(state["user_message"], state.get("client_context"))
        state["intent_result"] = result
        state.setdefault("decision_log", []).append(f"intent={result.intent}:{result.confidence}")
        return state

    def route_from_intent(self, state: WorkflowState) -> str:
        result = state["intent_result"]
        if result.risk_level == "high":
            return "handoff"
        if result.intent == "unknown" or result.confidence < 0.45:
            return "fallback"
        return "policy_guard"

    def policy_guard(self, state: WorkflowState) -> WorkflowState:
        auth = state["auth_context"]
        result = state["intent_result"]

        if result.intent in FAQ_INTENTS:
            if "kb:read" not in auth.permissions:
                raise HTTPException(status_code=403, detail="Missing kb:read permission")
            state["route_after_policy"] = "faq_rag"
            return state

        if result.intent == "personal_report":
            if "report:read:self" not in auth.permissions and "report:read:any" not in auth.permissions:
                raise HTTPException(status_code=403, detail="Missing report permission")
            state["route_after_policy"] = "report_fetch"
            return state

        state["route_after_policy"] = "handoff"
        return state

    def route_after_policy(self, state: WorkflowState) -> str:
        return state["route_after_policy"]

    def faq_rag(self, state: WorkflowState) -> WorkflowState:
        result = rag_service.answer_query(state["db"], state["user_message"], state.get("client_context"))
        state["final_answer"] = result.answer
        state["citations"] = result.citations
        state.setdefault("decision_log", []).append("faq_rag")
        audit_service.log(
            state["db"],
            action="faq_rag",
            detail={"used_fallback": result.used_fallback},
            user_id=state["auth_context"].user_id,
            thread_id=state.get("thread_id"),
        )
        return state

    def report_fetch(self, state: WorkflowState) -> WorkflowState:
        auth = state["auth_context"]
        result = state["intent_result"]
        month = result.resolved_month
        if not month:
            month = report_service.latest_month_for_user(state["db"], auth.user_id)
            if not month:
                state["final_answer"] = "未提供月份，且系统中没有可用报告记录。"
                return state

        user, report = report_service.fetch_report(
            state["db"],
            auth,
            month=month,
            target_account_code=result.target_account_code,
        )
        state["report_payload"] = {"user": user, "report": report}
        state["citations"] = []
        audit_service.log(
            state["db"],
            action="report_fetch",
            detail={"month": month, "target_account_code": user.account_code},
            user_id=auth.user_id,
            thread_id=state.get("thread_id"),
        )
        return state

    def report_generate(self, state: WorkflowState) -> WorkflowState:
        payload = state.get("report_payload")
        if not payload:
            state["final_answer"] = state.get("final_answer", "未找到足够依据。")
            return state
        state["final_answer"] = report_service.generate_report_markdown(payload["user"], payload["report"])
        state.setdefault("decision_log", []).append("report_generate")
        return state

    def fallback(self, state: WorkflowState) -> WorkflowState:
        result = state.get("intent_result")
        if result and result.required_entities:
            state["final_answer"] = f"需要补充这些信息后才能继续：{', '.join(result.required_entities)}。"
        else:
            state["final_answer"] = "当前无法稳定识别该请求，建议补充更具体的问题或转人工处理。"
        state["citations"] = []
        return state

    def handoff(self, state: WorkflowState) -> WorkflowState:
        state["final_answer"] = "该请求存在越权或高风险特征，已建议转人工处理。"
        state["citations"] = []
        return state


workflow_engine = WorkflowEngine()
