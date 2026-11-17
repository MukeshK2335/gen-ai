from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRelevancyMetric,
    GEval
)
from deepeval.models import GeminiModel
from dotenv import load_dotenv
import os
from day3_llm_rag import ask_question
load_dotenv()
 
eval_model = GeminiModel(
    model="gemini-3.5-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)


def test_llm_answer_relevancy():

    question = "How much money did Binance lose in the hack?"

    #actual_answer = ask_question(question)
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

    #assert_test(test_case, [metric])
    metric.measure(test_case)
    print("->-"*50)
    print(f"Answer Relevancy Score: {metric.score}")
    print(f"Threshold: {metric.threshold}")
    print(f"Success: {metric.is_successful()}")
    print(f"Reason: {metric.reason}")
    assert metric.is_successful()

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

def test_rag_quality():
    question = "What happened in the Binance hack?"
    result = ask_question(question)
    actual_answer = result["answer"]
    retrieved_text = result["retrieval_context"]
 
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
    validation_chain = RunnableParallel(
       answer_relevancy=RunnableLambda(lambda _: run_metric(answer_metric, test_case)),
       faithfulness=RunnableLambda(lambda _: run_metric(faithfulness, test_case)),
       contextual_relevancy=RunnableLambda(lambda _: run_metric(contextual_relevancy, test_case)),
    )
 
    validation_chain.invoke({})
    from langfuse import get_client
    load_dotenv()
 
    langfuse = get_client()
    trace_id = result["trace_id"]
 
    langfuse.create_score(
        trace_id=trace_id,
        name="answer_relevancy",
        value=float(answer_metric.score),
        comment=answer_metric.reason,
        data_type="NUMERIC"
    )
    langfuse.create_score(
            trace_id=trace_id,
            name="faithfulness",
            value=float(faithfulness.score),
            comment=faithfulness.reason,
            data_type="NUMERIC"
    )
    print(f"contextual_relevancy Relevancy Score: {contextual_relevancy.score}")
    print(f"Threshold: {contextual_relevancy.threshold}")
    print(f"Success: {contextual_relevancy.is_successful()}")
    print(f"Reason: {contextual_relevancy.reason}")
 
    langfuse.create_score(
            trace_id=trace_id,
            name="contextual_relevancy",
            value=float(contextual_relevancy.score),
            comment=contextual_relevancy.reason,
            data_type="NUMERIC"
    )

    
    #assert_test(test_case, [answer_metric, faithfulness, contextual_relevancy])
    # assert_test(test_case, [answer_metric, faithfulness, contextual_relevancy])
    #answer_metric.measure(test_case)
    #faithfulness.measure(test_case)
    #contextual_relevancy.measure(test_case)
 
    #print(f"Answer Relevancy Score: {answer_metric.score}")
    #print(f"Threshold: {answer_metric.threshold}")
    #print(f"Success: {answer_metric.is_successful()}")
    #print(f"Reason: {answer_metric.reason}")
 
    #print(f"faithfulness Relevancy Score: {faithfulness.score}")
    #print(f"Threshold: {faithfulness.threshold}")
    #print(f"Success: {faithfulness.is_successful()}")
    #print(f"Reason: {faithfulness.reason}")
    #print(f"contextual_relevancy Relevancy Score: {contextual_relevancy.score}")
    #print(f"Threshold: {contextual_relevancy.threshold}")
    #print(f"Success: {contextual_relevancy.is_successful()}")
    #print(f"Reason: {contextual_relevancy.reason}")



def test_llm_answer_groundedness():

    question = "How much money did Binance lose in the hack?"

    result = ask_question(question)

    actual_answer = result["answer"]

    retrieval_context = [result["retrieval_context"]]
 
    test_case = LLMTestCase(

        input=question,

        actual_output=actual_answer,

        retrieval_context=retrieval_context

    )

    from deepeval.test_case import LLMTestCaseParams

    groundedness_eval = GEval(

        name = "custom_evaluator",

        criteria=   "The answer is factually grounded in the provided context and does not contain hallucinations. The answer directly addresses the user's question.",           

        model=eval_model,

        evaluation_params=[

                LLMTestCaseParams.INPUT,

                LLMTestCaseParams.ACTUAL_OUTPUT,

                LLMTestCaseParams.RETRIEVAL_CONTEXT

            ],

        threshold=0.7,

    )
 
    groundedness_eval.measure(test_case)
 
    score = groundedness_eval.score

    print(f"... G-eval score is {score} and reason is {groundedness_eval.reason}")

    assert groundedness_eval.is_successful()
 