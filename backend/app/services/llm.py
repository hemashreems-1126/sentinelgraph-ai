import json
import logging
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class GroqLLMService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.is_mock = settings.is_mock_llm
        self._client = None

        if not self.is_mock and self.api_key:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
                logger.info(f"Initialized live Groq LLM client with model: {self.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}. Falling back to offline mock mode.")
                self.is_mock = True

    def _call_groq(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        if self.is_mock or not self._client:
            raise RuntimeError("Running in mock mode")

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Groq API call failed ({e}). Falling back to deterministic mock response.")
            raise

    # 1. Adaptive Investigation Planner
    def generate_adaptive_plan(self, alert: Dict[str, Any], prior_evidence: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        alert_type = alert.get("alert_type", "ANOMALY")
        entity_id = alert.get("entity_id", "UNKNOWN")
        severity = alert.get("severity", "MEDIUM")

        if not self.is_mock:
            try:
                sys_prompt = "You are an expert Financial Crime Investigation Lead. Return a structured JSON investigation plan."
                usr_prompt = f"""
                Generate an adaptive investigation plan for this alert:
                Alert Type: {alert_type}
                Entity ID: {entity_id}
                Severity: {severity}
                Prior Evidence: {json.dumps(prior_evidence or {})}
                
                Respond in JSON format:
                {{
                    "primary_objective": "...",
                    "required_data_sources": ["..."],
                    "planned_steps": [
                        {{"step_number": 1, "agent": "EvidenceRetrievalAgent", "objective": "..."}},
                        {{"step_number": 2, "agent": "GraphRelationshipAgent", "objective": "..."}},
                        {{"step_number": 3, "agent": "BehaviorAnalysisAgent", "objective": "..."}},
                        {{"step_number": 4, "agent": "DocumentAnalysisAgent", "objective": "..."}},
                        {{"step_number": 5, "agent": "ExternalIntelligenceAgent", "objective": "..."}},
                        {{"step_number": 6, "agent": "CaseAssemblyAgent", "objective": "..."}}
                    ],
                    "adaptation_reason": "Dynamic priority routing calibrated to severity and entity transaction topology."
                }}
                """
                content = self._call_groq(sys_prompt, usr_prompt)
                return json.loads(content)
            except Exception:
                pass

        # High-Fidelity Deterministic Fallback
        return {
            "planner_mode": "adaptive",
            "alert_type": alert_type,
            "primary_objective": f"Perform deep forensic investigation of {alert_type} on entity {entity_id} with multi-hop network expansion and behavioral baseline analysis.",
            "required_data_sources": [
                "Core Transaction Ledger (90-day)",
                "Entity Relationship Graph (2-hop)",
                "Historical Velocity Baselines",
                "KYC Verification Notes & Source of Wealth",
                "OFAC/PEP Intelligence Watchlists"
            ],
            "planned_steps": [
                {
                    "step_number": 1,
                    "agent": "EvidenceRetrievalAgent",
                    "objective": "Retrieve complete 90-day ledger history, historical alert records, and KYC profile."
                },
                {
                    "step_number": 2,
                    "agent": "GraphRelationshipAgent",
                    "objective": "Traverse 2-hop transaction network to uncover shell intermediaries, circular flows, or shared counterparty clusters."
                },
                {
                    "step_number": 3,
                    "agent": "BehaviorAnalysisAgent",
                    "objective": "Quantify deviation in transaction size, velocity z-scores, and sudden liquidity spikes against peer cohort."
                },
                {
                    "step_number": 4,
                    "agent": "DocumentAnalysisAgent",
                    "objective": "Extract and cross-verify declared occupation vs observed counterparty industry codes from unstructured KYC notes."
                },
                {
                    "step_number": 5,
                    "agent": "ExternalIntelligenceAgent",
                    "objective": "Screen subject and immediate counterparties against PEP, OFAC sanctions, and adverse media registers."
                },
                {
                    "step_number": 6,
                    "agent": "CaseAssemblyAgent",
                    "objective": "Synthesize all sub-agent findings into a consolidated case repository for final reasoning."
                }
            ],
            "adaptation_reason": f"Adaptive plan dynamically emphasized graph traversal and behavioral outlier z-scores due to {severity} risk trigger."
        }

    # 2. Hypothesis Generation Agent
    def generate_hypotheses(self, alert: Dict[str, Any], customer_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        alert_type = alert.get("alert_type", "ANOMALY")
        cust_name = customer_info.get("full_name", "Subject")
        occ = customer_info.get("occupation", "Professional")

        if not self.is_mock:
            try:
                sys_prompt = "You are an AML Intelligence Analyst. Formulate 2-3 plausible competing hypotheses in JSON."
                usr_prompt = f"""
                Generate 2 to 3 competing hypotheses for:
                Alert Type: {alert_type}
                Customer: {cust_name} (Occupation: {occ})
                Alert Details: {json.dumps(alert)}
                
                Respond in JSON:
                {{
                    "hypotheses": [
                        {{
                            "hypothesis_id": "H1",
                            "title": "...",
                            "description": "...",
                            "probability": 0.65,
                            "type": "SUSPICIOUS"
                        }},
                        {{
                            "hypothesis_id": "H2",
                            "title": "...",
                            "description": "...",
                            "probability": 0.35,
                            "type": "LEGITIMATE"
                        }}
                    ]
                }}
                """
                content = self._call_groq(sys_prompt, usr_prompt)
                parsed = json.loads(content)
                if "hypotheses" in parsed:
                    return parsed["hypotheses"]
            except Exception:
                pass

        # High-Fidelity Deterministic Fallback
        if alert_type == "STRUCTURING":
            return [
                {
                    "hypothesis_id": "H1",
                    "title": "Deliberate Cash Structuring (Smurfing) to Avoid PAN Reporting",
                    "description": f"Subject {cust_name} is orchestrating repeated cash deposits just beneath the ₹50,000 PAN-quoting threshold to avoid identification and conceal the source of funds.",
                    "probability": 0.72,
                    "type": "SUSPICIOUS"
                },
                {
                    "hypothesis_id": "H2",
                    "title": "Legitimate High-Volume Seasonal Commercial Revenue",
                    "description": f"Transactions reflect genuine commercial receivables consistent with {occ} operational cash flow split across multiple vendor invoices.",
                    "probability": 0.28,
                    "type": "LEGITIMATE"
                }
            ]
        elif alert_type == "LAYERING":
            return [
                {
                    "hypothesis_id": "H1",
                    "title": "Multi-Hop Pass-Through Layering Scheme",
                    "description": "Rapid pass-through of funds across intermediary accounts designed to obscure audit trail and disconnect origin from destination.",
                    "probability": 0.78,
                    "type": "SUSPICIOUS"
                },
                {
                    "hypothesis_id": "H2",
                    "title": "Inter-Company Liquidity Rebalancing",
                    "description": "Automated internal treasury transfers across corporate subsidiary accounts for payroll or liquidity optimization.",
                    "probability": 0.22,
                    "type": "LEGITIMATE"
                }
            ]
        elif alert_type == "UPI_MULE_CHAIN":
            return [
                {
                    "hypothesis_id": "H1",
                    "title": "UPI Money-Mule Account Collecting Scam Proceeds",
                    "description": "Many unrelated payers sent small UPI amounts that were moved onward within minutes — consistent with a mule account receiving fraud victims' money.",
                    "probability": 0.8,
                    "type": "SUSPICIOUS"
                },
                {
                    "hypothesis_id": "H2",
                    "title": "Account Holder is a Tricked or Recruited Victim",
                    "description": "The holder may have lent or sold account access (e.g. a fake 'job' offer) without understanding it — suspicious flow, but the response may differ (freeze and warn vs. criminal referral).",
                    "probability": 0.15,
                    "type": "SUSPICIOUS"
                },
                {
                    "hypothesis_id": "H3",
                    "title": "Legitimate Small Merchant or Group Collection",
                    "description": "A small shop or a group collection (e.g. event, rent split) receiving many UPI payments and settling them to a supplier.",
                    "probability": 0.05,
                    "type": "LEGITIMATE"
                }
            ]
        elif alert_type == "MULE_ACCOUNT":
            return [
                {
                    "hypothesis_id": "H1",
                    "title": "Compromised / Recruited Money Mule Conduit",
                    "description": "Recently dormant or low-activity personal account exhibiting sudden high-velocity inbound burst followed by immediate outbound dissipation.",
                    "probability": 0.81,
                    "type": "SUSPICIOUS"
                },
                {
                    "hypothesis_id": "H2",
                    "title": "One-Off Real Estate or Inheritance Influx",
                    "description": "Single legitimate windfall settlement disbursed into personal account followed by planned capital expenditure.",
                    "probability": 0.19,
                    "type": "LEGITIMATE"
                }
            ]
        elif alert_type == "VELOCITY_ABUSE":
            return [
                {
                    "hypothesis_id": "H1",
                    "title": "Automated Bot / Rapid Drain Attack",
                    "description": "Automated script executing micro-transactions in rapid succession to bypass single-transaction velocity controls.",
                    "probability": 0.75,
                    "type": "SUSPICIOUS"
                },
                {
                    "hypothesis_id": "H2",
                    "title": "Bulk Merchant Settlement or Payroll Batch",
                    "description": "System-generated batch disbursement triggered during normal billing cycle processing.",
                    "probability": 0.25,
                    "type": "LEGITIMATE"
                }
            ]
        else:
            return [
                {
                    "hypothesis_id": "H1",
                    "title": "Unexplained Behavioral Anomaly Consistent with Financial Crime",
                    "description": f"Statistical outlier in volume, counterparties, and timing inconsistent with historical profile for {cust_name}.",
                    "probability": 0.68,
                    "type": "SUSPICIOUS"
                },
                {
                    "hypothesis_id": "H2",
                    "title": "Normal Variance in Consumer Spending Behavior",
                    "description": "Infrequent but benign high-ticket personal purchase or emergency liquidity transfer.",
                    "probability": 0.32,
                    "type": "LEGITIMATE"
                }
            ]

    # 3. Analysis & Reasoning Agent
    def analyze_and_reason(
        self,
        assembled_case: Dict[str, Any],
        hypotheses: List[Dict[str, Any]],
        iteration_count: int
    ) -> Dict[str, Any]:
        if not self.is_mock:
            try:
                sys_prompt = "You are a Senior AML Forensics Investigator. Synthesize evidence, test hypotheses, and determine if further evidence is required."
                usr_prompt = f"""
                Assembled Case Data: {json.dumps(assembled_case)}
                Hypotheses: {json.dumps(hypotheses)}
                Current Iteration: {iteration_count}
                
                Respond in JSON:
                {{
                    "synthesis_summary": "...",
                    "evaluated_hypotheses": [
                        {{
                            "hypothesis_id": "H1",
                            "status": "SUPPORTED",
                            "updated_probability": 0.85,
                            "key_corroborating_facts": ["..."],
                            "contradicting_facts": ["..."]
                        }}
                    ],
                    "confidence_score": 0.88,
                    "needs_more_evidence": false,
                    "missing_evidence_reasons": []
                }}
                """
                content = self._call_groq(sys_prompt, usr_prompt)
                return json.loads(content)
            except Exception:
                pass

        # High-Fidelity Deterministic Fallback
        evidence = assembled_case.get("evidence", {})
        graph = assembled_case.get("graph_data", {})
        behavior = assembled_case.get("behavior_data", {})
        intel = assembled_case.get("intelligence_data", {})
        doc = assembled_case.get("document_data", {})
        
        is_high_risk = (
            graph.get("high_risk_connections_count", 0) > 0 or
            intel.get("sanctions_match", False) or
            intel.get("pep_match", False) or
            behavior.get("velocity_z_score", 0.0) > 2.5 or
            behavior.get("amount_z_score", 0.0) > 2.0
        )

        needs_loop = False
        missing_reasons = []
        if iteration_count < 1 and not intel.get("screened", False):
            needs_loop = True
            missing_reasons.append("External intelligence screening incomplete for secondary counterparties.")

        h1_prob = 0.84 if is_high_risk else 0.22
        h2_prob = 1.0 - h1_prob

        return {
            "synthesis_summary": (
                (f"Preliminary synthesis: the evidence leans towards H1 (suspicious). " if is_high_risk
                 else f"Preliminary synthesis: the evidence does not clearly support H1; a legitimate explanation remains plausible. ")
                + f"The final file / don't-file decision is made by the deterministic Filing Decision agent from evidence-linked red flags. "
                f"Graph analysis detected {graph.get('total_counterparties', 0)} counterparties with {graph.get('high_risk_connections_count', 0)} flagged hops. "
                f"Behavioral z-score velocity stands at {behavior.get('velocity_z_score', 0.0):.2f}, indicating significant statistical deviation from customer baseline."
            ),
            "evaluated_hypotheses": [
                {
                    "hypothesis_id": "H1",
                    "status": "SUPPORTED" if is_high_risk else "REFUTED",
                    "updated_probability": round(h1_prob, 2),
                    "key_corroborating_facts": [
                        f"Velocity z-score: {behavior.get('velocity_z_score', 0.0):.2f} exceeds threshold",
                        f"Graph shortest path to high risk cluster: {graph.get('shortest_path_to_watchlist', 'N/A')}",
                        f"Adverse intelligence flags: {intel.get('flag_summary', 'None')}"
                    ],
                    "contradicting_facts": [
                        "Declared KYC occupation partially aligns with transaction description"
                    ]
                },
                {
                    "hypothesis_id": "H2",
                    "status": "REFUTED" if is_high_risk else "SUPPORTED",
                    "updated_probability": round(h2_prob, 2),
                    "key_corroborating_facts": [
                        "Valid KYC verification status on file"
                    ],
                    "contradicting_facts": [
                        f"Unusually high outbound pass-through ratio of {behavior.get('outbound_ratio', 0.85)*100:.1f}% within 24h"
                    ]
                }
            ],
            "confidence_score": 0.89,
            "needs_more_evidence": needs_loop,
            "missing_evidence_reasons": missing_reasons
        }

    # 4. SAR / Report Drafting Agent
    # 6. STR narrative drafting — the LLM may only re-word evidence-linked claims
    MODUS_OPERANDI = {
        "UPI_MULE_CHAIN": (
            "Several unrelated individuals transferred small amounts to the subject account through UPI. "
            "Shortly afterwards the balance was moved onward to other accounts, leaving little behind. "
            "This is consistent with the account being used as a money-mule conduit for scam proceeds."
        ),
        "STRUCTURING": (
            "Cash was deposited in a series of amounts kept just below the PAN-quoting threshold, which avoids "
            "identification of the depositor. Splitting deposits this way is a recognised structuring typology."
        ),
        "MULE_ACCOUNT": (
            "A large credit was received and almost the same amount was sent out again soon after, so the account "
            "acted as a pass-through rather than holding the funds for any stated purpose."
        ),
        "LAYERING": (
            "Funds were passed through a chain of accounts in quick succession, each forwarding most of what it "
            "received. This obscures the link between where the money came from and where it ends up."
        ),
        "VELOCITY_ABUSE": (
            "A burst of transactions was made within a very short time, which is inconsistent with ordinary "
            "personal or business activity and suggests automated or coordinated movement of funds."
        ),
        "FAN_IN_AGGREGATION": (
            "Funds from many different accounts were collected into the subject account, a pattern used to pool "
            "proceeds before moving them on."
        ),
        "FAN_OUT_DISPERSION": (
            "Funds were spread from the subject account to many different beneficiaries, a pattern used to break up "
            "proceeds and make them harder to trace."
        ),
    }

    def draft_str_narrative(
        self,
        fact_sheet: Dict[str, Any],
        alert: Dict[str, Any],
        customer: Dict[str, Any],
        decision: Dict[str, Any],
    ) -> Dict[str, Any]:
        alert_type = alert.get("alert_type", "ANOMALY")
        base_claims = [dict(c) for c in fact_sheet.get("claims", [])]
        modus = self.MODUS_OPERANDI.get(
            alert_type,
            "The activity is a statistical outlier compared with the customer's usual behaviour and declared profile.",
        )

        if not self.is_mock and base_claims:
            try:
                sys_prompt = (
                    "You are a compliance officer drafting an STR for FIU-IND. Rewrite each claim in clear, formal "
                    "English. Keep claim_id, evidence_ids and assertions EXACTLY as given. Use only numbers that "
                    "appear in that claim's assertions. Do not add new facts. Return JSON."
                )
                usr_prompt = json.dumps({
                    "alert_type": alert_type,
                    "decision": decision.get("decision"),
                    "claims": [{k: c[k] for k in ("claim_id", "text", "evidence_ids", "assertions")} for c in base_claims],
                    "respond_with": {"claims": [{"claim_id": "...", "text": "..."}],
                                     "modus_operandi": "2-3 sentences, NO numbers"},
                })
                parsed = json.loads(self._call_groq(sys_prompt, usr_prompt))
                rewritten = {c.get("claim_id"): c.get("text") for c in parsed.get("claims", [])}
                for c in base_claims:
                    # Only the wording may change; evidence and assertions always come from the fact sheet.
                    if rewritten.get(c["claim_id"]):
                        c["text"] = rewritten[c["claim_id"]]
                return {
                    "claims": base_claims,
                    "modus_operandi": parsed.get("modus_operandi") or modus,
                    "drafted_by": f"llm:{self.model}",
                }
            except Exception:
                pass

        return {"claims": base_claims, "modus_operandi": modus, "drafted_by": "deterministic-template"}


llm_service = GroqLLMService()
