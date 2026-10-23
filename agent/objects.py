from pydantic import BaseModel, Field


class Answer(BaseModel):
    answer: str = Field(description="The answer provided by the model")
    conversation: bool = Field(
        description="This is an indicator to know if the conversation is ongoing or not",
        default=True,
    )


class PurchaseItem(BaseModel):
    name: str = Field(min_length=1, description="The exact name of the purchased item")
    # quantity: int = Field(description="The quantity of the item to be purchased", default=1)
