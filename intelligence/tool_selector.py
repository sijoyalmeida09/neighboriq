"""Tool Selector — unbiased AI/automation tool recommendations with cost math.

Recommends the objectively best tool for each task regardless of vendor.
If Gemini beats Claude, we say so. If DeepSeek beats GPT-4o, we say so.
Every recommendation is backed by exact pricing, context window, and speed data.
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "LLMSpec",
    "AutomationToolSpec",
    "AgentFrameworkSpec",
    "VectorDBSpec",
    "ToolRecommendation",
    "recommend_llm",
    "recommend_automation",
    "recommend_agent_framework",
    "recommend_vector_db",
    "full_stack_recommendation",
    "format_recommendation",
    "list_llms",
    "list_automation_tools",
]

# ── Data models ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LLMSpec:
    provider: str
    model_id: str
    alias: str
    context_window_k: int        # thousands of tokens
    input_cost_per_m: float      # $ per 1M input tokens
    output_cost_per_m: float     # $ per 1M output tokens
    tokens_per_second: int
    supports_function_calling: bool
    supports_vision: bool
    supports_audio: bool
    self_hostable: bool
    data_stays_local: bool       # True only when self-hosted
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    best_use_cases: tuple[str, ...]


@dataclass(frozen=True)
class AutomationToolSpec:
    name: str
    vendor: str
    monthly_cost_free: float
    monthly_cost_paid: float
    self_hostable: bool
    integrations_count: int
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    best_use_cases: tuple[str, ...]
    not_good_for: tuple[str, ...]


@dataclass(frozen=True)
class AgentFrameworkSpec:
    name: str
    vendor: str
    license: str                 # "MIT", "Apache-2.0", "proprietary"
    monthly_cost: float          # $0 for OSS
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    best_use_cases: tuple[str, ...]


@dataclass(frozen=True)
class VectorDBSpec:
    name: str
    vendor: str
    monthly_cost_free: float
    monthly_cost_paid: float
    self_hostable: bool
    max_vectors_free: int        # 0 = unlimited self-hosted
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    best_for_scale: tuple[str, ...]  # "prototype", "small", "medium", "large"


@dataclass(frozen=True)
class ToolRecommendation:
    task: str
    winner: str
    winner_reason: str
    runner_up: str
    runner_up_reason: str
    cost_winner: str
    cost_analysis: str
    avoid: str
    key_tradeoff: str


# ── LLM catalogue (mid-2026 pricing) ──────────────────────────────────────────

_LLMS: list[LLMSpec] = [
    # ── Anthropic ──────────────────────────────────────────────────────────────
    LLMSpec(
        provider="Anthropic", model_id="claude-haiku-4-5-20251001",
        alias="Claude Haiku 4.5",
        context_window_k=200, input_cost_per_m=0.25, output_cost_per_m=1.25,
        tokens_per_second=120,
        supports_function_calling=True, supports_vision=True, supports_audio=False,
        self_hostable=False, data_stays_local=False,
        strengths=("bulk classification", "simple extraction", "cheap batch tasks", "fast"),
        weaknesses=("complex multi-step reasoning", "architecture decisions"),
        best_use_cases=("high-volume text classification", "simple entity extraction",
                        "quick summarization", "cheap background agents"),
    ),
    LLMSpec(
        provider="Anthropic", model_id="claude-sonnet-4-6",
        alias="Claude Sonnet 4.6",
        context_window_k=200, input_cost_per_m=3.0, output_cost_per_m=15.0,
        tokens_per_second=80,
        supports_function_calling=True, supports_vision=True, supports_audio=False,
        self_hostable=False, data_stays_local=False,
        strengths=("complex instruction following", "agentic workflows", "code review",
                   "multi-file reasoning", "tool use reliability"),
        weaknesses=("expensive at scale", "smaller context than Gemini"),
        best_use_cases=("agentic coding assistants", "multi-step reasoning chains",
                        "complex instruction following", "code generation and review"),
    ),
    LLMSpec(
        provider="Anthropic", model_id="claude-opus-4-7",
        alias="Claude Opus 4.7",
        context_window_k=200, input_cost_per_m=15.0, output_cost_per_m=75.0,
        tokens_per_second=40,
        supports_function_calling=True, supports_vision=True, supports_audio=False,
        self_hostable=False, data_stays_local=False,
        strengths=("architecture decisions", "ambiguous requirements", "deep analysis",
                   "nuanced judgment"),
        weaknesses=("very expensive", "overkill for routine tasks", "slow"),
        best_use_cases=("system architecture planning", "complex ambiguous problem solving",
                        "high-stakes decision support"),
    ),
    # ── Google ─────────────────────────────────────────────────────────────────
    LLMSpec(
        provider="Google", model_id="gemini-1.5-flash",
        alias="Gemini 1.5 Flash",
        context_window_k=1000, input_cost_per_m=0.075, output_cost_per_m=0.30,
        tokens_per_second=150,
        supports_function_calling=True, supports_vision=True, supports_audio=True,
        self_hostable=False, data_stays_local=False,
        strengths=("1M token context window", "large document analysis", "multilingual",
                   "cheap at scale", "video/audio understanding"),
        weaknesses=("weaker on complex reasoning vs Sonnet", "occasional hallucinations on facts"),
        best_use_cases=("entire codebase indexing", "long PDF analysis", "video transcription",
                        "bulk processing needing >200K context"),
    ),
    LLMSpec(
        provider="Google", model_id="gemini-1.5-pro",
        alias="Gemini 1.5 Pro",
        context_window_k=1000, input_cost_per_m=1.25, output_cost_per_m=5.0,
        tokens_per_second=80,
        supports_function_calling=True, supports_vision=True, supports_audio=True,
        self_hostable=False, data_stays_local=False,
        strengths=("complex reasoning WITH large context", "audio understanding",
                   "video analysis", "only model doing both well"),
        weaknesses=("expensive vs Flash for simple tasks"),
        best_use_cases=("large codebase reasoning", "long-form document QA",
                        "audio/video analysis with complex follow-up"),
    ),
    LLMSpec(
        provider="Google", model_id="gemini-2.0-flash",
        alias="Gemini 2.0 Flash",
        context_window_k=1000, input_cost_per_m=0.10, output_cost_per_m=0.40,
        tokens_per_second=160,
        supports_function_calling=True, supports_vision=True, supports_audio=True,
        self_hostable=False, data_stays_local=False,
        strengths=("1M context", "fastest Google model", "multimodal", "cheapest large-context"),
        weaknesses=("newer — ecosystem integrations still maturing"),
        best_use_cases=("large document bulk processing", "cheap extraction at scale",
                        "real-time multimodal tasks"),
    ),
    LLMSpec(
        provider="Google", model_id="gemini-2.5-pro",
        alias="Gemini 2.5 Pro",
        context_window_k=1000, input_cost_per_m=3.50, output_cost_per_m=10.50,
        tokens_per_second=60,
        supports_function_calling=True, supports_vision=True, supports_audio=True,
        self_hostable=False, data_stays_local=False,
        strengths=("deepest reasoning in Google family", "best Google model for complex tasks",
                   "1M context + strong reasoning"),
        weaknesses=("expensive", "slower than Flash variants"),
        best_use_cases=("complex analysis over large documents",
                        "architecture decisions needing large codebase context"),
    ),
    # ── OpenAI ─────────────────────────────────────────────────────────────────
    LLMSpec(
        provider="OpenAI", model_id="gpt-4o",
        alias="GPT-4o",
        context_window_k=128, input_cost_per_m=5.0, output_cost_per_m=15.0,
        tokens_per_second=80,
        supports_function_calling=True, supports_vision=True, supports_audio=True,
        self_hostable=False, data_stays_local=False,
        strengths=("best-in-class function calling reliability", "structured JSON output",
                   "broadest plugin ecosystem", "voice mode", "ChatGPT compatibility"),
        weaknesses=("expensive", "128K context much smaller than Gemini"),
        best_use_cases=("reliable function calling", "structured JSON extraction",
                        "OpenAI-ecosystem integrations", "voice applications"),
    ),
    LLMSpec(
        provider="OpenAI", model_id="gpt-4o-mini",
        alias="GPT-4o mini",
        context_window_k=128, input_cost_per_m=0.15, output_cost_per_m=0.60,
        tokens_per_second=120,
        supports_function_calling=True, supports_vision=True, supports_audio=False,
        self_hostable=False, data_stays_local=False,
        strengths=("cheap GPT-4 quality", "massive ecosystem compatibility",
                   "reliable structured output"),
        weaknesses=("128K context limit", "weaker on complex reasoning"),
        best_use_cases=("OpenAI-ecosystem apps on budget", "simple structured extraction",
                        "chatbots needing GPT compatibility"),
    ),
    LLMSpec(
        provider="OpenAI", model_id="o3-mini",
        alias="o3-mini",
        context_window_k=128, input_cost_per_m=1.10, output_cost_per_m=4.40,
        tokens_per_second=20,
        supports_function_calling=True, supports_vision=False, supports_audio=False,
        self_hostable=False, data_stays_local=False,
        strengths=("math and scientific reasoning", "better than o1 on many benchmarks",
                   "cost-effective deep reasoning", "multi-step logic"),
        weaknesses=("slow", "no vision", "small context"),
        best_use_cases=("competitive math/science problems", "financial modeling",
                        "code correctness proofs", "complex algorithm design"),
    ),
    LLMSpec(
        provider="OpenAI", model_id="o1",
        alias="o1",
        context_window_k=128, input_cost_per_m=15.0, output_cost_per_m=60.0,
        tokens_per_second=15,
        supports_function_calling=True, supports_vision=True, supports_audio=False,
        self_hostable=False, data_stays_local=False,
        strengths=("deepest OpenAI reasoning", "PhD-level scientific tasks"),
        weaknesses=("very expensive", "very slow", "overkill for most tasks"),
        best_use_cases=("hardest math/science problems where o3-mini fails",
                        "complex multi-step proofs"),
    ),
    # ── Meta (Open Source) ─────────────────────────────────────────────────────
    LLMSpec(
        provider="Meta (Open Source)", model_id="meta-llama/Llama-3.1-8B-Instruct",
        alias="Llama 3.1 8B",
        context_window_k=128, input_cost_per_m=0.05, output_cost_per_m=0.08,
        tokens_per_second=200,
        supports_function_calling=True, supports_vision=False, supports_audio=False,
        self_hostable=True, data_stays_local=True,
        strengths=("free self-hosted", "privacy — data never leaves server",
                   "fastest open-source", "zero cost on owned GPU"),
        weaknesses=("quality below GPT-4o for complex tasks", "no vision"),
        best_use_cases=("privacy-sensitive local inference", "offline deployments",
                        "high-volume cheap classification with owned hardware"),
    ),
    LLMSpec(
        provider="Meta (Open Source)", model_id="meta-llama/Llama-3.1-70B-Instruct",
        alias="Llama 3.1 70B",
        context_window_k=128, input_cost_per_m=0.30, output_cost_per_m=0.40,
        tokens_per_second=60,
        supports_function_calling=True, supports_vision=False, supports_audio=False,
        self_hostable=True, data_stays_local=True,
        strengths=("best open-source quality-to-cost", "close to GPT-4o on many tasks",
                   "self-hostable", "GDPR-friendly"),
        weaknesses=("needs ~40GB VRAM to self-host", "no vision"),
        best_use_cases=("enterprise deployments requiring data sovereignty",
                        "GDPR-compliant EU applications", "cost-sensitive at scale"),
    ),
    LLMSpec(
        provider="Meta (Open Source)", model_id="meta-llama/Llama-3.2-11B-Vision",
        alias="Llama 3.2 Vision",
        context_window_k=128, input_cost_per_m=0.16, output_cost_per_m=0.16,
        tokens_per_second=80,
        supports_function_calling=True, supports_vision=True, supports_audio=False,
        self_hostable=True, data_stays_local=True,
        strengths=("open-source vision", "free self-hosted", "privacy-safe image analysis"),
        weaknesses=("weaker than GPT-4o Vision on complex visual tasks"),
        best_use_cases=("private image analysis", "self-hosted document OCR",
                        "CCTV/camera analysis without cloud"),
    ),
    # ── Mistral ────────────────────────────────────────────────────────────────
    LLMSpec(
        provider="Mistral", model_id="mistral-large-latest",
        alias="Mistral Large",
        context_window_k=128, input_cost_per_m=4.0, output_cost_per_m=12.0,
        tokens_per_second=70,
        supports_function_calling=True, supports_vision=False, supports_audio=False,
        self_hostable=False, data_stays_local=False,
        strengths=("EU-hosted GDPR compliance", "French/Spanish/Italian language",
                   "reliable function calling", "European data residency"),
        weaknesses=("no vision", "expensive", "smaller ecosystem"),
        best_use_cases=("European GDPR-compliant apps", "multilingual EU products",
                        "French-language tasks"),
    ),
    LLMSpec(
        provider="Mistral", model_id="codestral-latest",
        alias="Codestral",
        context_window_k=128, input_cost_per_m=0.20, output_cost_per_m=0.60,
        tokens_per_second=100,
        supports_function_calling=False, supports_vision=False, supports_audio=False,
        self_hostable=False, data_stays_local=False,
        strengths=("code completion specifically optimized", "VS Code/Cursor integration",
                   "fill-in-the-middle for code"),
        weaknesses=("code-only — not general purpose", "no function calling"),
        best_use_cases=("IDE code completion", "inline code suggestions",
                        "autocomplete for code editors"),
    ),
    # ── Other ──────────────────────────────────────────────────────────────────
    LLMSpec(
        provider="DeepSeek", model_id="deepseek-chat",
        alias="DeepSeek V3",
        context_window_k=128, input_cost_per_m=0.14, output_cost_per_m=0.28,
        tokens_per_second=90,
        supports_function_calling=True, supports_vision=False, supports_audio=False,
        self_hostable=True, data_stays_local=False,
        strengths=("cheapest frontier-quality model", "excellent coding and math",
                   "strong reasoning at low price"),
        weaknesses=("data goes to China-based servers (privacy concern)",
                    "no vision", "geopolitical risk for sensitive data"),
        best_use_cases=("cost-sensitive coding tasks where data isn't sensitive",
                        "math and algorithmic work on budget"),
    ),
    LLMSpec(
        provider="DeepSeek", model_id="deepseek-reasoner",
        alias="DeepSeek R1",
        context_window_k=128, input_cost_per_m=0.55, output_cost_per_m=2.19,
        tokens_per_second=25,
        supports_function_calling=False, supports_vision=False, supports_audio=False,
        self_hostable=True, data_stays_local=False,
        strengths=("cheap o1 alternative", "strong math and reasoning",
                   "chain-of-thought transparency"),
        weaknesses=("China-hosted data privacy concern", "slow", "no function calling"),
        best_use_cases=("budget math/science reasoning", "algorithmic problem solving",
                        "o1-alternative when cost matters more than data privacy"),
    ),
    LLMSpec(
        provider="Alibaba (Open Source)", model_id="Qwen/Qwen2.5-72B-Instruct",
        alias="Qwen 2.5 72B",
        context_window_k=128, input_cost_per_m=0.50, output_cost_per_m=0.50,
        tokens_per_second=70,
        supports_function_calling=True, supports_vision=False, supports_audio=False,
        self_hostable=True, data_stays_local=True,
        strengths=("best Chinese language model", "strong coding", "very cheap via API",
                   "self-hostable"),
        weaknesses=("Chinese company — data sovereignty considerations",
                    "less ecosystem support than OpenAI/Anthropic"),
        best_use_cases=("Chinese-language applications", "Asian market products",
                        "budget coding tasks"),
    ),
    LLMSpec(
        provider="Perplexity", model_id="sonar",
        alias="Perplexity Sonar",
        context_window_k=128, input_cost_per_m=1.0, output_cost_per_m=1.0,
        tokens_per_second=60,
        supports_function_calling=False, supports_vision=False, supports_audio=False,
        self_hostable=False, data_stays_local=False,
        strengths=("internet search built-in", "current web data without separate search step",
                   "citations included"),
        weaknesses=("can't replace structured reasoning", "no function calling",
                    "dependent on web quality"),
        best_use_cases=("tasks needing current web data", "market research queries",
                        "news-aware applications"),
    ),
]

_LLM_BY_ALIAS: dict[str, LLMSpec] = {m.alias: m for m in _LLMS}

# ── Automation tools catalogue ─────────────────────────────────────────────────

_AUTOMATION: list[AutomationToolSpec] = [
    AutomationToolSpec(
        name="n8n", vendor="n8n GmbH",
        monthly_cost_free=0.0, monthly_cost_paid=20.0,
        self_hostable=True, integrations_count=400,
        strengths=("free self-hosted unlimited executions", "complex multi-step workflows",
                   "developer-controlled", "privacy-first", "best power-to-cost ratio"),
        weaknesses=("requires server to self-host", "steeper learning curve than Zapier"),
        best_use_cases=("complex developer workflows", "self-hosted privacy-first automation",
                        "high-volume automations on budget", "open-source control"),
        not_good_for=("non-technical users who need zero setup",),
    ),
    AutomationToolSpec(
        name="Make.com", vendor="Celonis",
        monthly_cost_free=0.0, monthly_cost_paid=9.0,
        self_hostable=False, integrations_count=1500,
        strengths=("best visual workflow builder UI", "non-technical friendly",
                   "1500+ app integrations", "good EU data handling"),
        weaknesses=("gets expensive at volume", "less logic power than n8n",
                    "not self-hostable"),
        best_use_cases=("visual workflow design by non-technical teams",
                        "medium-volume business automations", "EU-compliant automations"),
        not_good_for=("high-volume automations (cost scales fast)",
                      "developer-controlled complex logic"),
    ),
    AutomationToolSpec(
        name="Zapier", vendor="Zapier Inc.",
        monthly_cost_free=0.0, monthly_cost_paid=20.0,
        self_hostable=False, integrations_count=6000,
        strengths=("broadest app coverage — 6000+ apps", "most non-technical-friendly",
                   "largest automation marketplace"),
        weaknesses=("most expensive per task", "limited conditional logic vs n8n",
                    "not self-hostable"),
        best_use_cases=("connecting obscure apps with no other integration option",
                        "simple 2-step automations for non-technical users"),
        not_good_for=("complex logic", "high-volume automations (prohibitively expensive)",
                      "developer control"),
    ),
    AutomationToolSpec(
        name="Activepieces", vendor="Activepieces",
        monthly_cost_free=0.0, monthly_cost_paid=9.0,
        self_hostable=True, integrations_count=200,
        strengths=("n8n alternative with cleaner codebase", "growing fast",
                   "free self-hosted", "MIT license"),
        weaknesses=("fewer integrations than n8n yet", "smaller community"),
        best_use_cases=("n8n alternative for cleaner self-hosted setup",
                        "open-source workflow automation"),
        not_good_for=("edge case integrations not yet built",),
    ),
    AutomationToolSpec(
        name="Temporal", vendor="Temporal Technologies",
        monthly_cost_free=0.0, monthly_cost_paid=50.0,
        self_hostable=True, integrations_count=10,
        strengths=("durable execution — survives crashes", "long-running workflow reliability",
                   "built-in retry logic", "enterprise-grade"),
        weaknesses=("complex setup", "overkill for simple automations",
                    "requires coding knowledge"),
        best_use_cases=("mission-critical workflows that must not lose state",
                        "long-running processes (hours/days)", "distributed systems coordination"),
        not_good_for=("simple trigger-action automations", "non-developer users"),
    ),
    AutomationToolSpec(
        name="Node-RED", vendor="IBM / OpenJS Foundation",
        monthly_cost_free=0.0, monthly_cost_paid=0.0,
        self_hostable=True, integrations_count=300,
        strengths=("purpose-built for IoT and edge", "Raspberry Pi ready",
                   "visual flow for hardware events", "free and open source"),
        weaknesses=("not great for cloud API workflows", "older UI",
                    "smaller non-IoT ecosystem"),
        best_use_cases=("IoT device automation", "Raspberry Pi projects",
                        "MQTT/hardware event processing"),
        not_good_for=("cloud SaaS integrations", "non-IoT business workflows"),
    ),
]

# ── Agent frameworks ───────────────────────────────────────────────────────────

_AGENT_FRAMEWORKS: list[AgentFrameworkSpec] = [
    AgentFrameworkSpec(
        name="LangGraph", vendor="LangChain Inc.", license="MIT", monthly_cost=0.0,
        strengths=("fine-grained stateful control", "complex agent loops",
                   "production reliability", "graph-based execution"),
        weaknesses=("most verbose to write", "steeper learning curve"),
        best_use_cases=("production multi-agent systems", "complex state machines",
                        "agents requiring precise control over execution flow"),
    ),
    AgentFrameworkSpec(
        name="CrewAI", vendor="CrewAI", license="MIT", monthly_cost=0.0,
        strengths=("fastest to set up", "role-based agent definitions",
                   "intuitive multi-agent collaboration"),
        weaknesses=("less execution control than LangGraph",
                    "abstraction hides important details"),
        best_use_cases=("rapid prototyping of multi-agent workflows",
                        "role-based agent teams", "quick demos"),
    ),
    AgentFrameworkSpec(
        name="AutoGen", vendor="Microsoft", license="MIT", monthly_cost=0.0,
        strengths=("code execution agents", "multi-agent conversations with code",
                   "automated data analysis pipelines"),
        weaknesses=("complex configuration", "less intuitive than CrewAI"),
        best_use_cases=("automated data analysis", "coding agents that run code",
                        "multi-agent code review workflows"),
    ),
    AgentFrameworkSpec(
        name="smolagents", vendor="HuggingFace", license="Apache-2.0", monthly_cost=0.0,
        strengths=("code-based agents", "works with any HuggingFace model",
                   "open-source model compatible"),
        weaknesses=("smaller ecosystem than LangGraph/CrewAI"),
        best_use_cases=("open-source model agent workflows",
                        "HuggingFace ecosystem integration"),
    ),
    AgentFrameworkSpec(
        name="Direct API (no framework)", vendor="Various", license="N/A", monthly_cost=0.0,
        strengths=("zero overhead", "full control", "easiest to debug",
                   "no dependency on framework decisions"),
        weaknesses=("you implement everything yourself"),
        best_use_cases=("simple single-agent tasks", "when framework overhead > benefit",
                        "tasks under 30 seconds with clear logic"),
    ),
]

# ── Vector databases ───────────────────────────────────────────────────────────

_VECTOR_DBS: list[VectorDBSpec] = [
    VectorDBSpec(
        name="Pinecone", vendor="Pinecone Systems",
        monthly_cost_free=0.0, monthly_cost_paid=70.0,
        self_hostable=False, max_vectors_free=100_000,
        strengths=("fastest managed search", "zero ops overhead",
                   "auto-scaling", "easiest managed production"),
        weaknesses=("vendor lock-in", "expensive at scale", "not self-hostable"),
        best_for_scale=("small", "medium"),
    ),
    VectorDBSpec(
        name="Qdrant", vendor="Qdrant",
        monthly_cost_free=0.0, monthly_cost_paid=25.0,
        self_hostable=True, max_vectors_free=0,
        strengths=("best OSS production option", "Rust performance",
                   "advanced payload filtering", "self-hosted free unlimited"),
        weaknesses=("requires ops for self-hosting"),
        best_for_scale=("small", "medium", "large"),
    ),
    VectorDBSpec(
        name="Weaviate", vendor="Weaviate B.V.",
        monthly_cost_free=0.0, monthly_cost_paid=25.0,
        self_hostable=True, max_vectors_free=0,
        strengths=("multi-modal text+image+audio", "hybrid search keyword+vector",
                   "GraphQL API", "module ecosystem"),
        weaknesses=("more complex setup than Qdrant"),
        best_for_scale=("small", "medium", "large"),
    ),
    VectorDBSpec(
        name="Chroma", vendor="Chroma",
        monthly_cost_free=0.0, monthly_cost_paid=0.0,
        self_hostable=True, max_vectors_free=0,
        strengths=("zero setup", "in-memory or local disk", "perfect for prototyping",
                   "Python-native"),
        weaknesses=("not production-ready at scale", "no clustering"),
        best_for_scale=("prototype",),
    ),
    VectorDBSpec(
        name="pgvector", vendor="PostgreSQL ecosystem",
        monthly_cost_free=0.0, monthly_cost_paid=0.0,
        self_hostable=True, max_vectors_free=0,
        strengths=("already in Postgres", "no extra service", "SQL joins with vectors",
                   "zero additional cost"),
        weaknesses=("not suitable >1M vectors", "approximate search quality lower than dedicated DBs"),
        best_for_scale=("prototype", "small"),
    ),
    VectorDBSpec(
        name="Milvus", vendor="Zilliz",
        monthly_cost_free=0.0, monthly_cost_paid=65.0,
        self_hostable=True, max_vectors_free=0,
        strengths=("billion-scale vectors", "enterprise-grade", "GPU acceleration"),
        weaknesses=("complex setup", "overkill for <10M vectors"),
        best_for_scale=("large",),
    ),
]

# ── Fast lookup tables ─────────────────────────────────────────────────────────

_KNOWN_BEST_LLM: dict[str, str] = {
    "large_document_analysis":       "Gemini 1.5 Flash",
    "long_codebase_indexing":        "Gemini 1.5 Pro",
    "function_calling_reliability":  "GPT-4o",
    "structured_json_output":        "GPT-4o",
    "privacy_sensitive_local":       "Llama 3.1 70B",
    "math_scientific_reasoning":     "o3-mini",
    "cheap_bulk_classification":     "Gemini 2.0 Flash",
    "european_gdpr_compliance":      "Mistral Large",
    "chinese_language":              "Qwen 2.5 72B",
    "code_completion_ide":           "Codestral",
    "cheapest_frontier_code":        "DeepSeek V3",
    "web_search_included":           "Perplexity Sonar",
    "complex_agentic_workflows":     "Claude Sonnet 4.6",
    "architecture_planning":         "Claude Opus 4.7",
    "vision_privacy":                "Llama 3.2 Vision",
}

_KNOWN_BEST_AUTOMATION: dict[str, str] = {
    "simple_automation":             "Zapier",
    "complex_automation_cheap":      "n8n",
    "europe_automation":             "Make.com",
    "iot_edge":                      "Node-RED",
    "durable_workflows":             "Temporal",
    "budget_self_hosted":            "n8n",
}

_KNOWN_BEST_FRAMEWORK: dict[str, str] = {
    "quick_agents":                  "CrewAI",
    "production_agents":             "LangGraph",
    "code_execution_agents":         "AutoGen",
    "open_source_model_agents":      "smolagents",
    "simple_single_agent":           "Direct API (no framework)",
}

_KNOWN_BEST_VECTOR: dict[str, str] = {
    "prototype":                     "Chroma",
    "small":                         "Qdrant",
    "medium":                        "Qdrant",
    "large":                         "Milvus",
    "already_have_postgres":         "pgvector",
    "managed_no_ops":                "Pinecone",
}

# ── Keyword scorer ─────────────────────────────────────────────────────────────

def _score_llm(task: str, llm: LLMSpec) -> int:
    task_lower = task.lower()
    score = 0
    for keyword in llm.strengths + llm.best_use_cases:
        if any(word in task_lower for word in keyword.lower().split()):
            score += 1
    return score


def _score_automation(task: str, tool: AutomationToolSpec) -> int:
    task_lower = task.lower()
    score = 0
    for keyword in tool.strengths + tool.best_use_cases:
        if any(word in task_lower for word in keyword.lower().split()):
            score += 1
    for bad in tool.not_good_for:
        if any(word in task_lower for word in bad.lower().split()):
            score -= 2
    return score


# ── Public API ─────────────────────────────────────────────────────────────────

def recommend_llm(
    task_description: str,
    constraints: dict | None = None,
) -> ToolRecommendation:
    """Recommend the best LLM for a task with full cost justification."""
    c = constraints or {}
    max_cost = c.get("max_cost_per_m", 9999.0)
    min_ctx  = c.get("min_context_k", 0)
    need_self_host = c.get("requires_self_host", False)
    need_vision = c.get("requires_vision", False)
    need_fc = c.get("requires_function_calling", False)
    privacy = c.get("privacy_required", False)

    # Apply hard constraints
    candidates = [
        m for m in _LLMS
        if m.input_cost_per_m <= max_cost
        and m.context_window_k >= min_ctx
        and (not need_self_host or m.self_hostable)
        and (not need_vision or m.supports_vision)
        and (not need_fc or m.supports_function_calling)
        and (not privacy or m.data_stays_local)
    ]
    if not candidates:
        candidates = _LLMS  # fallback: ignore constraints

    ranked = sorted(candidates, key=lambda m: _score_llm(task_description, m), reverse=True)
    winner = ranked[0]
    runner = ranked[1] if len(ranked) > 1 else winner

    cheapest = min(candidates, key=lambda m: m.input_cost_per_m)

    # Cost comparison: winner vs most expensive plausible alternative
    expensive = max(candidates, key=lambda m: m.input_cost_per_m)
    if expensive == winner:
        expensive = min(candidates, key=lambda m: -m.input_cost_per_m)
    ratio = (expensive.input_cost_per_m / winner.input_cost_per_m) if winner.input_cost_per_m > 0 else 1.0
    cost_analysis = (
        f"{winner.alias}: ${winner.input_cost_per_m}/M in, ${winner.output_cost_per_m}/M out. "
        f"{expensive.alias} costs ${expensive.input_cost_per_m}/M in — "
        f"{ratio:.0f}x more expensive for the same task."
    )

    avoid = expensive
    avoid_reason = (
        f"{avoid.alias} (${avoid.input_cost_per_m}/M) — {ratio:.0f}x more expensive "
        f"with no quality advantage for '{task_description[:40]}'"
    )

    return ToolRecommendation(
        task=task_description,
        winner=f"{winner.alias} ({winner.provider})",
        winner_reason=(
            f"{', '.join(winner.strengths[:3])}. "
            f"Context: {winner.context_window_k}K tokens. "
            f"${winner.input_cost_per_m}/M in."
        ),
        runner_up=f"{runner.alias} ({runner.provider})",
        runner_up_reason=(
            f"${runner.input_cost_per_m}/M in, {runner.context_window_k}K ctx. "
            f"{runner.strengths[0] if runner.strengths else ''}."
        ),
        cost_winner=f"{cheapest.alias} (${cheapest.input_cost_per_m}/M in)",
        cost_analysis=cost_analysis,
        avoid=avoid_reason,
        key_tradeoff=(
            f"{winner.provider} vs {runner.provider} ecosystem lock-in. "
            f"Pick {winner.alias} unless you have existing {runner.provider} infrastructure."
        ),
    )


def recommend_automation(
    task_description: str,
    constraints: dict | None = None,
) -> ToolRecommendation:
    """Recommend the best automation tool with cost and capability justification."""
    c = constraints or {}
    need_self_host = c.get("requires_self_host", False)

    candidates = [
        t for t in _AUTOMATION
        if not need_self_host or t.self_hostable
    ]

    ranked = sorted(candidates, key=lambda t: _score_automation(task_description, t), reverse=True)
    winner = ranked[0]
    runner = ranked[1] if len(ranked) > 1 else winner
    cheapest = min(candidates, key=lambda t: t.monthly_cost_paid)

    return ToolRecommendation(
        task=task_description,
        winner=winner.name,
        winner_reason=(
            f"{', '.join(winner.strengths[:3])}. "
            f"${winner.monthly_cost_paid}/mo paid tier, {winner.integrations_count}+ integrations."
        ),
        runner_up=runner.name,
        runner_up_reason=(
            f"${runner.monthly_cost_paid}/mo, {runner.integrations_count}+ integrations. "
            f"{runner.strengths[0] if runner.strengths else ''}."
        ),
        cost_winner=f"{cheapest.name} (${cheapest.monthly_cost_paid}/mo)",
        cost_analysis=(
            f"{winner.name}: ${winner.monthly_cost_free}/mo free, ${winner.monthly_cost_paid}/mo paid. "
            f"Self-hostable: {'yes' if winner.self_hostable else 'no'}."
        ),
        avoid=f"Zapier at scale — most expensive per task ($0.05-0.10/task), hits $50+/mo fast",
        key_tradeoff=(
            "Self-hosted (n8n/Activepieces) = $0/mo unlimited but needs a server. "
            "Managed (Make/Zapier) = instant setup but costs grow with volume."
        ),
    )


def recommend_agent_framework(task_description: str) -> ToolRecommendation:
    """Recommend the best agent framework for a given use case."""
    task_lower = task_description.lower()

    ranked = sorted(
        _AGENT_FRAMEWORKS,
        key=lambda f: sum(
            1 for kw in f.strengths + f.best_use_cases
            if any(w in task_lower for w in kw.lower().split())
        ),
        reverse=True,
    )
    winner = ranked[0]
    runner = ranked[1] if len(ranked) > 1 else winner

    return ToolRecommendation(
        task=task_description,
        winner=winner.name,
        winner_reason=f"{', '.join(winner.strengths[:3])}. License: {winner.license}.",
        runner_up=runner.name,
        runner_up_reason=f"{runner.strengths[0] if runner.strengths else ''}.",
        cost_winner=f"Direct API (no framework) — $0, zero overhead",
        cost_analysis="All listed frameworks are free/OSS. Cost is developer time, not licensing.",
        avoid=(
            "LangChain (base) for new projects — LangGraph supersedes it. "
            "Avoid heavyweight frameworks for tasks solvable with a plain function + API call."
        ),
        key_tradeoff=(
            f"Framework overhead vs control. {winner.name} gives more "
            f"{'control' if 'LangGraph' in winner.name else 'speed'} — "
            "pick Direct API if your task fits in <50 lines of Python."
        ),
    )


def recommend_vector_db(
    scale: str,
    constraints: dict | None = None,
) -> ToolRecommendation:
    """Recommend vector DB by scale: 'prototype'|'small'|'medium'|'large'."""
    c = constraints or {}
    need_self_host = c.get("requires_self_host", False)
    has_postgres = c.get("already_have_postgres", False)
    managed_ok = c.get("managed_ok", True)

    if has_postgres and scale in ("prototype", "small"):
        winner_name = "pgvector"
    elif scale == "prototype":
        winner_name = "Chroma"
    elif scale == "large":
        winner_name = "Milvus"
    elif need_self_host or not managed_ok:
        winner_name = "Qdrant"
    else:
        winner_name = "Qdrant"  # best OSS default

    winner = next((v for v in _VECTOR_DBS if v.name == winner_name), _VECTOR_DBS[0])
    runner = next(
        (v for v in _VECTOR_DBS if v.name != winner_name and scale in v.best_for_scale),
        _VECTOR_DBS[1],
    )

    return ToolRecommendation(
        task=f"Vector database for {scale} scale",
        winner=winner.name,
        winner_reason=(
            f"{', '.join(winner.strengths[:3])}. "
            f"${winner.monthly_cost_paid}/mo paid. Self-hostable: {'yes' if winner.self_hostable else 'no'}."
        ),
        runner_up=runner.name,
        runner_up_reason=f"{', '.join(runner.strengths[:2])}.",
        cost_winner=f"Chroma (prototype) or pgvector (if you have Postgres) — $0",
        cost_analysis=(
            f"{winner.name}: ${winner.monthly_cost_free}/mo free tier, "
            f"${winner.monthly_cost_paid}/mo paid. "
            f"Pinecone managed: $70+/mo. Qdrant self-hosted: $0."
        ),
        avoid=(
            "Pinecone at >10M vectors — costs $200+/mo. "
            "pgvector at >1M vectors — ANN quality degrades."
        ),
        key_tradeoff="Managed (Pinecone) = zero ops, high cost. Self-hosted (Qdrant) = ops overhead, $0.",
    )


def full_stack_recommendation(
    business_description: str,
    use_case: str,
) -> dict[str, ToolRecommendation]:
    """Return tool recommendations for the full AI stack based on business + use case."""
    combined = f"{business_description} {use_case}"

    # Heuristic: detect scale signals
    scale = "small"
    if any(w in combined.lower() for w in ("million", "billion", "enterprise", "billion")):
        scale = "large"
    elif any(w in combined.lower() for w in ("startup", "mvp", "prototype", "demo")):
        scale = "prototype"
    elif any(w in combined.lower() for w in ("medium", "growing", "1000", "10000")):
        scale = "medium"

    # Detect constraints
    privacy = any(w in combined.lower() for w in ("hipaa", "gdpr", "private", "sensitive", "confidential"))
    needs_large_ctx = any(w in combined.lower() for w in ("codebase", "entire", "large pdf", "transcript", "long"))

    llm_constraints: dict = {}
    if privacy:
        llm_constraints["privacy_required"] = True
    if needs_large_ctx:
        llm_constraints["min_context_k"] = 500

    return {
        "llm": recommend_llm(combined, llm_constraints),
        "automation": recommend_automation(combined),
        "agent_framework": recommend_agent_framework(combined),
        "vector_db": recommend_vector_db(scale, {"already_have_postgres": "postgres" in combined.lower()}),
    }


def format_recommendation(rec: ToolRecommendation) -> str:
    """Format a ToolRecommendation for CLI display."""
    width = 60
    bar = "─" * width
    lines = [
        f"┌{bar}┐",
        f"│ TOOL RECOMMENDATION{' ' * (width - 19)}│",
        f"│ {rec.task[:width - 2]:<{width - 2}}│",
        f"├{bar}┤",
        f"│ WINNER      {rec.winner[:width - 14]:<{width - 14}}│",
    ]
    # Wrap winner_reason
    reason_words = rec.winner_reason.split()
    line = ""
    for word in reason_words:
        if len(line) + len(word) + 1 > width - 14:
            lines.append(f"│             {line:<{width - 14}}│")
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(f"│             {line:<{width - 14}}│")

    lines += [
        f"├{bar}┤",
        f"│ RUNNER-UP   {rec.runner_up[:width - 14]:<{width - 14}}│",
        f"│             {rec.runner_up_reason[:width - 14]:<{width - 14}}│",
        f"├{bar}┤",
        f"│ CHEAPEST    {rec.cost_winner[:width - 14]:<{width - 14}}│",
        f"│ COST MATH   {rec.cost_analysis[:width - 14]:<{width - 14}}│",
        f"├{bar}┤",
        f"│ AVOID       {rec.avoid[:width - 14]:<{width - 14}}│",
        f"├{bar}┤",
        f"│ KEY TRADEOFF{' ' * (width - 13)}│",
    ]
    tradeoff_words = rec.key_tradeoff.split()
    line = ""
    for word in tradeoff_words:
        if len(line) + len(word) + 1 > width - 2:
            lines.append(f"│ {line:<{width - 2}}│")
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(f"│ {line:<{width - 2}}│")

    lines.append(f"└{bar}┘")
    return "\n".join(lines)


def list_llms() -> list[str]:
    return [f"{m.alias} ({m.provider}) — in:${m.input_cost_per_m}/M ctx:{m.context_window_k}K" for m in _LLMS]


def list_automation_tools() -> list[str]:
    return [f"{t.name} ({t.vendor}) — paid:${t.monthly_cost_paid}/mo integrations:{t.integrations_count}" for t in _AUTOMATION]
