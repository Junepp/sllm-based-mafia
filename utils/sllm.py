from langchain_openai import ChatOpenAI


def get_sllm_instance(model_name, model_endpoint):
    sllm = ChatOpenAI(
        model=model_name,
        base_url=model_endpoint,
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
    # mn = "/home/jhjun/models/kanana-nano-2.1b-instruct/"
    # ep = "http://127.0.0.1:8000/v1"
    
    mn = "/app/models/kanana-nano-2.1b-instruct/"
    ep = "http://192.168.105.26:8008/v1"
    
    retval = get_sllm_instance(model_name=mn, model_endpoint=ep)
    print(retval)
    
    response = retval.invoke("너는 누구니?")
    print(response.content)
    