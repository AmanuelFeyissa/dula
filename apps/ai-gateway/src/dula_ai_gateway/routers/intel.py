"""Cyber-intelligence endpoints (Phase 05): CTI extraction, vulnerability analysis, and
detection authoring/validation.

The heavy lifting is deterministic and offline (``dula_ai.intel``): IOC/TTP extraction, STIX
mapping, CVSS scoring, and Sigma/YARA authoring with validation. Only the optional CTI summary
uses the LLM Gateway, subject to the same budget/guardrails. All authored rules are validated
before return, so responses are syntactically valid and reviewable.
"""

from __future__ import annotations

from typing import Any

from dula_ai.gateway import BudgetExceeded
from dula_ai.intel import vuln as vulnmod
from dula_ai.intel.attack import Technique
from dula_ai.intel.cti import CTIService
from dula_ai.intel.detections import coverage as covmod
from dula_ai.intel.detections import sigma, yara
from dula_ai.intel.iocs import Indicator, extract
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from dula_ai_gateway.deps import Context, Subsystem, require

router = APIRouter(prefix="/api/v1/intel", tags=["intel"])


# ---- CTI extraction (UC-05) -------------------------------------------------------------


class ExtractRequest(BaseModel):
    advisory: str = Field(min_length=1, max_length=40_000)
    summarize: bool = True


class IndicatorOut(BaseModel):
    kind: str
    value: str
    defanged: str


class TechniqueOut(BaseModel):
    id: str
    name: str
    tactic: str


class ExtractResponse(BaseModel):
    indicators: list[IndicatorOut]
    techniques: list[TechniqueOut]
    stix_bundle: dict[str, Any]
    summary: str | None
    input_flags: list[str]


def _ind_out(ind: Indicator) -> IndicatorOut:
    return IndicatorOut(kind=ind.kind, value=ind.value, defanged=ind.defanged)


def _tech_out(t: Technique) -> TechniqueOut:
    return TechniqueOut(id=t.id, name=t.name, tactic=t.tactic)


@router.post("/extract", response_model=ExtractResponse, dependencies=[Depends(require("ai.cti"))])
async def extract_cti(data: ExtractRequest, ctx: Context, subsystem: Subsystem) -> ExtractResponse:
    svc = CTIService(gateway=subsystem.gateway if data.summarize else None)
    try:
        result = await svc.extract(
            advisory=data.advisory,
            tenant=ctx.tenant,
            subject=ctx.subject,
            summarize=data.summarize,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except BudgetExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    return ExtractResponse(
        indicators=[_ind_out(i) for i in result.indicators],
        techniques=[_tech_out(t) for t in result.techniques],
        stix_bundle=result.stix_bundle,
        summary=result.summary,
        input_flags=result.input_flags,
    )


# ---- Vulnerability analysis (UC-07) -----------------------------------------------------


class VulnRequest(BaseModel):
    cvss_vector: str = Field(min_length=3, max_length=128)
    cve_id: str | None = Field(default=None, max_length=32)
    known_exploited: bool = False
    internet_facing: bool = False
    asset_criticality: str = Field(default="medium", pattern="^(low|medium|high)$")
    patch_available: bool = True


class VulnResponse(BaseModel):
    cve_id: str | None
    base_score: float
    severity: str
    priority: str
    risk_score: float
    rationale: list[str]
    metrics: dict[str, str]


@router.post(
    "/vulnerability", response_model=VulnResponse, dependencies=[Depends(require("ai.vuln"))]
)
async def analyze_vulnerability(data: VulnRequest, ctx: Context) -> VulnResponse:
    try:
        cvss = vulnmod.parse_cvss_vector(data.cvss_vector)
    except vulnmod.CvssError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    signals = vulnmod.Signals(
        known_exploited=data.known_exploited,
        internet_facing=data.internet_facing,
        asset_criticality=data.asset_criticality,
        patch_available=data.patch_available,
    )
    p = vulnmod.prioritize(cvss.base_score, signals)
    return VulnResponse(
        cve_id=data.cve_id,
        base_score=cvss.base_score,
        severity=cvss.severity.value,
        priority=p.priority.value,
        risk_score=p.risk_score,
        rationale=p.rationale,
        metrics=cvss.metrics,
    )


# ---- Detection authoring + validation (UC-04) -------------------------------------------


class SigmaAuthorRequest(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    advisory: str = Field(min_length=1, max_length=40_000)
    category: str | None = None
    product: str | None = None
    service: str | None = None
    attack_tags: list[str] = Field(default_factory=list)
    level: str = Field(default="high")


class RuleResponse(BaseModel):
    rule: str
    valid: bool
    errors: list[str]
    warnings: list[str]


def _http_no_indicators(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post(
    "/detections/sigma", response_model=RuleResponse, dependencies=[Depends(require("ai.detect"))]
)
async def author_sigma(data: SigmaAuthorRequest, ctx: Context) -> RuleResponse:
    indicators = extract(data.advisory)
    try:
        _, text, result = sigma.build_ioc_rule(
            title=data.title,
            indicators=indicators,
            logsource=sigma.LogSource(data.category, data.product, data.service),
            attack_tags=data.attack_tags,
            level=data.level,
        )
    except ValueError as exc:
        raise _http_no_indicators(exc) from exc
    return RuleResponse(
        rule=text, valid=result.valid, errors=result.errors, warnings=result.warnings
    )


class YaraAuthorRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    advisory: str = Field(min_length=1, max_length=40_000)
    tags: list[str] = Field(default_factory=list)


@router.post(
    "/detections/yara", response_model=RuleResponse, dependencies=[Depends(require("ai.detect"))]
)
async def author_yara(data: YaraAuthorRequest, ctx: Context) -> RuleResponse:
    indicators = extract(data.advisory)
    try:
        _, text, result = yara.build_ioc_rule(name=data.name, indicators=indicators, tags=data.tags)
    except ValueError as exc:
        raise _http_no_indicators(exc) from exc
    return RuleResponse(
        rule=text, valid=result.valid, errors=result.errors, warnings=result.warnings
    )


class ValidateRequest(BaseModel):
    format: str = Field(pattern="^(sigma|yara)$")
    rule: str = Field(min_length=1, max_length=40_000)


class ValidationResponse(BaseModel):
    valid: bool
    errors: list[str]


@router.post(
    "/detections/validate",
    response_model=ValidationResponse,
    dependencies=[Depends(require("ai.detect"))],
)
async def validate_rule(data: ValidateRequest, ctx: Context) -> ValidationResponse:
    """Validate an externally-supplied (e.g. model-drafted) Sigma or YARA rule."""
    result = (
        sigma.validate_text(data.rule) if data.format == "sigma" else yara.validate_text(data.rule)
    )
    return ValidationResponse(valid=result.valid, errors=result.errors)


class CoverageRequest(BaseModel):
    rule_tag_sets: list[list[str]]
    target: list[str] | None = None


class CoverageResponse(BaseModel):
    covered_techniques: list[TechniqueOut]
    covered_tactics: list[str]
    gaps: list[str]
    coverage_ratio: float


@router.post(
    "/detections/coverage",
    response_model=CoverageResponse,
    dependencies=[Depends(require("ai.detect"))],
)
async def attack_coverage(data: CoverageRequest, ctx: Context) -> CoverageResponse:
    report = covmod.coverage(data.rule_tag_sets, target=data.target)
    return CoverageResponse(
        covered_techniques=[_tech_out(t) for t in report.covered_techniques],
        covered_tactics=report.covered_tactics,
        gaps=report.gaps,
        coverage_ratio=report.coverage_ratio,
    )
