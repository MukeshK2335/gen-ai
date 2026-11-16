from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.models import GeminiModel
from dotenv import load_dotenv
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRelevancyMetric
)
import os

from day3_llm_rag import ask_question
from langchain_core.runnables import RunnableParallel, RunnableLambda
 
def run_metric(metric, test_case):
    metric.measure(test_case)
    print("..>.." * 50)
    print(f"score: {metric.score}, reason: {metric.reason}")
    return {
       "score": metric.score,
       "threshold": metric.threshold,
       "success": metric.is_successful(),
       "reason": metric.reason
   }
load_dotenv()
 
eval_model = GeminiModel(
    model="gemini-3.5-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)

def test_llm_answer_relevancy():
    question = "How much money did Binance lose in the hack?"
    result = ask_question(question)
    actual_answer = result["answer"]

    test_case = LLMTestCase(
        input=question,
        actual_output=actual_answer
    )

    metric = AnswerRelevancyMetric(       
        threshold=0.5,       
        model=eval_model
        )
    assert_test(test_case, [metric])
    metric.measure(test_case)

    print(f"Answer Relevancy Score: {metric.score}")
    print(f"Threshold: {metric.threshold}")
    print(f"Success: {metric.is_successful()}")
    print(f"Reason: {metric.reason}")

    assert metric.is_successful()


def test_rag_quality():

    question = "What happened in the Binance hack?"

    result = ask_question(question)

    actual_answer = result["answer"]

    retrieved_text = result["retrieval_context"]

    print(type(retrieved_text))

    print("..>.." * 50)

    print(retrieved_text)

    test_case = LLMTestCase(

        input=question,

        actual_output=actual_answer,

        retrieval_context=[retrieved_text]

    )
 
    answer_metric = AnswerRelevancyMetric(

        threshold=0.5,

        model=eval_model

    )
 
    faithfulness = FaithfulnessMetric(

        threshold=0.7,

        model=eval_model

    )
 
    contextual_relevancy = ContextualRelevancyMetric(

        threshold=0.6,

        model=eval_model

    )
 
    assert_test(test_case, [answer_metric, faithfulness, contextual_relevancy])
