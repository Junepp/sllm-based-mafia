import yaml
from box import Box
from langchain_openai import ChatOpenAI


def get_sllm_instance():
    with open("config.yaml", "r") as f:
        config_yaml = yaml.load(f, Loader=yaml.FullLoader)
        config = Box(config_yaml)
    
    sllm = ChatOpenAI(
        model=config.sllm_model,
        base_url=config.sllm_endpoint,
        api_key="empty",
        temperature=1
    )
    
    try:
        response = sllm.invoke("test message")
        # print(response)
        
        return sllm
        
    except Exception as e:
        print("[ERR] llm connection failed")
        
        return None


if __name__ == "__main__":
    retval = get_sllm_instance()
    