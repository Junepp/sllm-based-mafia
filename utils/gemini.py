import yaml
from langchain_google_genai import ChatGoogleGenerativeAI

def get_gemini_instance():
    with open("gemini_key.yaml", "r") as f:
        config_yaml = yaml.load(f, Loader=yaml.FullLoader)
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",
        api_key=config_yaml["key"],
        temperature=1.0
    )
    
    try:
        response = llm.invoke("test message")
        # print(response)
        
        return llm
        
    except Exception as e:
        print("[ERR] llm connection failed")
        
        return None


if __name__ == "__main__":
    retval = get_gemini_instance()
    
    response = retval.invoke("너는 누구니?")
    print(response.content)
    
    # output_stream = retval.stream("너는 누구니?")
    # for chunk in output_stream:
    #     print(chunk.content, end="