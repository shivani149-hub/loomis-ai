from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(
        default="healthy",
        description="Current operational status of the service",
        examples=["healthy"],
    )
    service: str = Field(
        default="loomis-ai-backend",
        description="Name of the microservice",
        examples=["loomis-ai-backend"],
    )
    version: str = Field(
        default="0.1.0",
        description="Backend API semantic version",
        examples=["0.1.0"],
    )

