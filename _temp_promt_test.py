from langchain_core.prompts import load_prompt
from utils.sllm import get_sllm_instance

prompt = load_prompt("prompts/civil_decision_to_tell.yaml", encoding="utf-8")

llm = get_sllm_instance(
    model_name="/home/jhjun/models/kanana-nano-2.1b-instruct/",
    model_endpoint="http://127.0.0.1:8000/v1"
)
chain = prompt | llm

context = {
        "role": "침착한 관찰자",
        "description": "말이 많지 않지만 중요한 순간에만 입을 여는 타입. 조용히 상황을 지켜보며 필요한 정보를 수집하고, 결정적인 순간에 증거를 내놓는다. 하지만 너무 조용하면 존재감이 흐려져 오해를 받을 수 있다.",
        "stat": {
            "logic": 8,
            "intuition": 6,
            "trustworthiness": 7,
            "social_influence": 3,
            "adaptability": 6
        }
    }

context["name"] = "지훈"
# context = {
#     "name": "지훈",
#     "role": "논리적인 분석가",
#     "description": "냉철하고 논리적이며 이성적인 판단을 중시한다. 감정보다는 팩트와 증거를 바탕으로 결론을 내리며, 말수는 적지만 신뢰감을 주는 발언을 한다. 분석적인 사고로 게임을 주도하려고 한다."
# }

response = chain.invoke(context)
print("대답")
print(response.content)
