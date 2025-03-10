"""
    게임 구성요소
        1. 플레이어
        2. 가상 플레이어
        3. sllm (사회자 / 가상 플레이어 두뇌 /발언순서 조율)
    
    게임 옵션
        1. num_player (default=5): 플레이어 수 (유저 포함)
        2. limit_speak (default=20): 라운드당 발언 제한 수
        3. message_window_size (default=10)
            - 기억하는 발언의 수 = llm context
            - 증가시 llm 성능 저하 가능
        
"""

from utils.sllm import get_sllm_instance
from predefined_player.player import get_player

class Game:
    def __init__(self,
                 sllm_name,
                 sllm_endpoint,
                 num_player=5,
                 limit_speak=20,
                 message_window_size=10):
        
        # 게임 옵션
        self.players = get_player(num_player=num_player)
        self.limit_speak = limit_speak
        self.message_window_size = message_window_size
        
        # sllm 연결
        self.sllm = get_sllm_instance(
            model_name=sllm_name,
            model_endpoint=sllm_endpoint
            )
        
        self.message_history = []
    
    def choice_next_speaker(self):
        ...
        
    def round(self, ridx):
        print(f"\n{ridx}번째 아침이 밝았습니다. 자유롭게 토론해주세요")
    
    
