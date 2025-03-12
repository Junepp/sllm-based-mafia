"""
    게임 구성요소
        1. 플레이어
        2. 가상 플레이어
        3. sllm (사회자 / 가상 플레이어 두뇌 /발언순서 조율)
"""
import random
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
        self.num_player = num_player
        self.limit_speak = limit_speak
        self.message_window_size = message_window_size
        
        # 플레이어 초기화
        self.players = {}  # {name: {"role": str, "alive": bool}}
        self.init_players()
        
        # sllm 연결
        self.sllm = get_sllm_instance(
            model_name=sllm_name,
            model_endpoint=sllm_endpoint
        )
        
        self.message_history = []
        self.is_game_over = False
        
    def init_players(self):
        # 플레이어 할당
        players = get_player(num_player=self.num_player)
        
        # 마피아/시민 역할 분배
        num_mafia = max(1, self.num_player // 4)
        mafia_players = random.sample(players, num_mafia)
        
        for name in players:
            self.players[name] = {
                "role": "mafia" if name in mafia_players else "civil",
                "alive": True
            }
    
    def choice_next_speaker(self):
        """다음 발언자 선택"""
        alive_players = [name for name, info in self.players.items() 
                        if info["alive"]]
        
        # TODO: SLLM으로 다음 발언자 선택
        if alive_players:
            return random.choice(alive_players)
        return None
        
    def check_game_over(self):
        """게임 종료 조건 체크"""
        alive_mafia = len([1 for _, info in self.players.items() 
                          if info["role"] == "mafia" and info["alive"]])
        alive_civil = len([1 for _, info in self.players.items() 
                          if info["role"] == "civil" and info["alive"]])
        
        if alive_mafia == 0:
            print("시민 승리!")
            return True
        if alive_mafia >= alive_civil:
            print("마피아 승리!")
            return True
        return False
    
    def vote(self):
        """투표 진행"""
        # 투표 집계
        votes = {}
        alive_players = [name for name, info in self.players.items() 
                        if info["alive"]]
        
        for player in alive_players:
            vote_target = random.choice(alive_players)  # TODO: SLLM으로 대체
            votes[vote_target] = votes.get(vote_target, 0) + 1
        
        # 최다 득표자 처형
        max_votes = max(votes.values())
        executed = random.choice([p for p, v in votes.items() 
                                if v == max_votes])
        
        self.players[executed]["alive"] = False
        print(f"{executed}이(가) 투표로 처형되었습니다.")
        
    def night_phase(self):
        """밤 페이즈 - 마피아의 암살"""
        alive_mafia = [name for name, info in self.players.items() 
                      if info["role"] == "mafia" and info["alive"]]
        alive_civil = [name for name, info in self.players.items() 
                      if info["role"] == "civil" and info["alive"]]
        
        if alive_mafia and alive_civil:
            target = random.choice(alive_civil)  # TODO: SLLM으로 대체
            self.players[target]["alive"] = False
            print(f"\n{target}이(가) 밤중에 살해당했습니다.")
    
    def round(self, ridx):
        """라운드 진행"""
        print(f"\n{ridx}번째 아침이 밝았습니다.")
        
        # 토론
        speak_count = 0
        while speak_count < self.limit_speak:
            speaker = self.choice_next_speaker()
            if not speaker:
                break
                
            # TODO: SLLM으로 발언 생성
            speak_count += 1
            
        # 투표
        self.vote()
        
        if not self.check_game_over():
            # 밤
            print("\n밤이 되었습니다.")
            self.night_phase()
            self.check_game_over()
# 