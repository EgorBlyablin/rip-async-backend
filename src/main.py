import asyncio
import logging
import math
import httpx

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, PositiveInt

app = FastAPI()

TOKEN = "1234"
CALLBACK_URL = "https://backend:8000/api/generation-requests/callback"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TurbineCalcRequest(BaseModel):
    turbine_id: int
    avg_velocity: float
    height: int
    alpha: float
    power: int
    days: int


class GenerationCalcResponse(BaseModel):
    turbine_id: int
    calculated_generation: int


async def calculate_generation(
    generation_request_id: int, turbines: list[TurbineCalcRequest]
) -> None:
    logger.info("Waiting 10sec...")
    await asyncio.sleep(10)

    response: list[GenerationCalcResponse] = []

    optimal_velocity = 12.0
    cutoff_velocity = 15.0
    decrease_coefficient = 0.4

    for turbine in turbines:
        velocity_at_height = (
            turbine.avg_velocity * (turbine.height / 10.0) ** turbine.alpha
        )

        response.extend(
            (
                GenerationCalcResponse(
                    turbine_id=turbine.turbine_id,
                    calculated_generation=int(
                        turbine.power
                        * (velocity_at_height / optimal_velocity) ** 3
                        * math.exp(
                            -decrease_coefficient * velocity_at_height / cutoff_velocity
                        )
                        * 24
                        * turbine.days
                    ),
                ),
            )
        )

    async with httpx.AsyncClient(verify=False, follow_redirects=True) as client:
        try:
            update_result = await client.put(
                f"{CALLBACK_URL}/{generation_request_id}/",
                json=[r.model_dump() for r in response],
                headers={"Authorization": f"Token {TOKEN}"},
            )
            logger.info(f"Updated values: {update_result}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to send result: {e}")


@app.post("/calculate-generation/{generation_request_id}")
async def calculate_generation_handler(
    generation_request_id: PositiveInt,
    turbines: list[TurbineCalcRequest],
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    background_tasks.add_task(calculate_generation, generation_request_id, turbines)

    return {"message": "Calculation initiated"}
