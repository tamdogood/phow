from fastapi import APIRouter
from ...models.scenario_lab import ScenarioRunRequest
from ...services.scenario_lab_service import ScenarioLabService

router = APIRouter(prefix="/scenario-lab", tags=["scenario-lab"])


@router.post("/run")
async def run_scenario(request: ScenarioRunRequest):
    """Compute the profit / margin / break-even impact of a what-if scenario (stateless)."""
    base = request.base.model_dump(exclude_none=True) if request.base else {}
    return ScenarioLabService.run(base, request.overrides.model_dump())
