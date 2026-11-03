from pydantic import BaseModel, Field


class ImagePreprocessResponse(BaseModel):
    """Response payload for image upload and preprocessing."""

    success: bool = Field(
        default=True,
        description="Whether the preprocessing operation succeeded",
    )
    message: str = Field(
        default="Image preprocessed successfully.",
        description="Descriptive status message",
    )
    original_width: int = Field(
        ...,
        description="Original pixel width of the image prior to downsizing",
        examples=[1920],
    )
    original_height: int = Field(
        ...,
        description="Original pixel height of the image prior to downsizing",
        examples=[1080],
    )
    processed_width: int = Field(
        ...,
        description="Processed pixel width after constraining to max dimension (1024px)",
        examples=[1024],
    )
    processed_height: int = Field(
        ...,
        description="Processed pixel height after constraining to max dimension (1024px)",
        examples=[576],
    )
    original_format: str = Field(
        ...,
        description="Original format detected from the image file contents",
        examples=["JPEG"],
    )
    processed_format: str = Field(
        default="JPEG",
        description="Format of the output processed image",
        examples=["JPEG"],
    )
    image_base64: str = Field(
        ...,
        description="Base64-encoded JPEG image string",
    )
    processing_status: str = Field(
        default="success",
        description="High-level processing status indicator",
        examples=["success"],
    )

