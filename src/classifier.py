from pydantic import BaseModel, Field
from enum import Enum
from langchain_groq import ChatGroq

class IntentType(str, Enum):
    EXPLAIN = "Explain Code"
    GENERATE = "Generate Code"

class IntentSchema(BaseModel):
    intent: IntentType = Field(description="Classify whether the user wants code explained or generated.")

class RelevanceSchema(BaseModel):
    is_relevant: bool = Field(description="True if context contains information directly useful to answer the query, False otherwise.")
    reasoning: str = Field(description="Brief explanation of why the context is or isn't relevant.")

class WorkflowClassifier:
    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=os.environ.get("GROQ_API_KEY"),
            model_name="qwen-2.5-coder-32b",
            temperature=0.0
        )

    def classify_intent(self, query: str) -> IntentType:
        structured_llm = self.llm.with_structured_output(IntentSchema)
        res = structured_llm.invoke(f"Classify this request: '{query}'")
        return res.intent

    def check_relevance(self, query: str, context: str) -> bool:
        structured_llm = self.llm.with_structured_output(RelevanceSchema)
        prompt = f"Query: {query}\n\nRetrieved Context:\n{context}\n\nIs the context relevant?"
        res = structured_llm.invoke(prompt)
        return res.is_relevant