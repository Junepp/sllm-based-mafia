import random
from collections import deque
from utils.sllm import get_sllm_instance
from utils.gemini import get_gemini_instance
from predefined_player.player import get_player
from langchain_core.prompts import load_prompt


class Game:
    def __init__(self,
                 sllm_name,
                 sllm_endpoint,
                 num_player=5,
                 limit_speak=10,
                 message_window_size=10):
        
        # 게임 옵션
        self.num_player = num_player
        self.limit_speak = limit_speak
        self.message_window_size = message_window_size
        
        # 플레이어 초기화
        self.players = self.init_players()  # {name: {"role": str, "alive": bool}}
        
        # sllm 연결
        # self.sllm = get_sllm_instance(
        #     model_name=sllm_name,
        #     model_endpoint=sllm_endpoint
        # )
        
        self.sllm = get_gemini_instance()
        
        # 메시지 큐 (길이 10)
        self.message_history = deque(maxlen=message_window_size)
        self.is_game_over = False
        self.current_speaker = None
        
    def init_players(self):
        # 플레이어 지정
        players = get_player(num_player=self.num_player-1)
        players["나"] = {}
        
        # 마피아/시민 역할 분배
        num_mafia = max(1, self.num_player // 3)
        mafia_players = random.sample(players.keys(), num_mafia)
        
        for name in players.keys():
            players[name]["alive"] = True
            players[name]["role"] = "마피아" if name in mafia_players else "시민" # role 한글로 변경
            players[name]["type"] = "user" if name == "나" else "cpc"

        print(f"나는 {players['나']['role']} 이다!")
        
        return players
    
    def choice_next_speaker(self):
        """다음 발언자 선택 (SLLM 활용)"""
        
        if input("발언하시겠습니까? 아니면 enter"):
            return "나"
        
        alive_players = [name for name, info in self.players.items() 
                        if info["alive"]]
        
        if not alive_players:
            return None

        # TODO: SLLM을 활용하여 다음 발언자 선택
        prompt = load_prompt("prompts/choose_next_speaker.yaml", encoding="utf-8")

        speaker_info = {
            "player_info": {k:{"reputation":v["reputation"]} for k,v in self.players.items() if k != "나"},
            "message_history": self.message_history,
            "my_name": self.current_speaker
        }

        # print("####프롬프트=", prompt.invoke(speaker_info))
        
        chain = prompt | self.sllm
        response = chain.invoke(speaker_info)
        next_speaker = response.content
        # print("####출력:", next_speaker)

        # 현재 생존한 플레이어 중에 선택하도록 검증
        if next_speaker in alive_players:
            return next_speaker
        else:
            print(f"[WARN] {next_speaker} not in alive player. random choose")
            return random.choice(alive_players)

        
    def check_game_over(self):
        """게임 종료 조건 체크"""
        alive_mafia = len([1 for _, info in self.players.items() 
                          if info["role"] == "마피아" and info["alive"]])
        alive_civil = len([1 for _, info in self.players.items() 
                          if info["role"] == "시민" and info["alive"]])
        
        if alive_mafia == 0:
            print("시민 승리!")
            return True
        
        if alive_mafia >= alive_civil:
            print("마피아 승리!")
            return True
        
        return False
    
    def vote(self):
        """투표 진행 (SLLM 활용)"""
        # 투표 집계
        votes = {}
        alive_players = [name for name, info in self.players.items() 
                        if info["alive"]]
        
        for player in alive_players:
            
            if player == "나":
                vote_target = input("누구에게 투표하시겠습니까? : ")
                if vote_target not in alive_players:
                    print(f"[WARN] {vote_target} not in alive player. random choose")
                    vote_target = random.choice(alive_players)
            else:
                # TODO: SLLM을 사용하여 투표 대상 결정
                prompt = load_prompt("prompts/vote_decision.yaml", encoding="utf-8")
                player_info = self.players[player]
                context = {
                    "name": player,
                    "role": player_info["role"],
                    "reputation": player_info["reputation"],
                    "message_history": self.message_history,
                    "alive_players": alive_players
                }
                chain = prompt | self.sllm
                response = chain.invoke(context)
                vote_target = response.content

                if vote_target not in alive_players:
                    print(f"[WARN] {vote_target} not in alive player. random choose")
                    vote_target = random.choice(alive_players)
            
            votes[vote_target] = votes.get(vote_target, 0) + 1
        
        # 최다 득표자 처형
        max_votes = max(votes.values())
        executed = random.choice([p for p, v in votes.items() 
                                if v == max_votes])
        
        self.players[executed]["alive"] = False
        print(f"{executed}는(은) 투표로 처형되었습니다.")
        
    def night_phase(self):
        """밤 페이즈 - 마피아의 암살 (SLLM 활용)"""
        alive_mafia = [name for name, info in self.players.items() 
                      if info["role"] == "마피아" and info["alive"]]
        alive_civil = [name for name, info in self.players.items() 
                      if info["role"] == "시민" and info["alive"]]
        
        if alive_mafia and alive_civil:
            
            # 마피아가 2명 이상이면 서로 협의
            if len(alive_mafia) >= 2:
                prompt = load_prompt("prompts/mafia_discussion.yaml", encoding="utf-8")
                context = {
                    "mafia_names": alive_mafia,
                    "message_history": self.message_history,
                    "alive_civil": alive_civil
                }
                chain = prompt | self.sllm
                response = chain.invoke(context)
                print(f"[마피아협의]: {response.content}")

            target = random.choice(alive_civil)
            if "나" in alive_mafia:
                target = input("누구를 암살하시겠습니까?")
                if target not in alive_civil:
                    print("[ERR] 잘못된 입력입니다. 다시 입력해주세요.")
                    target = input("누구를 암살하시겠습니까? : ")
            else:
                prompt = load_prompt("prompts/mafia_kill_decision.yaml", encoding="utf-8")
                mafia = alive_mafia[0]
                context = {
                    "mafia_name": mafia,
                    "message_history": self.message_history,
                    "alive_civil": alive_civil
                }
                chain = prompt | self.sllm
                response = chain.invoke(context)
                target = response.content
            
            if target not in alive_civil:
                print(f"[WARN] {target} not in civil. random choose")
                target = random.choice(alive_civil)
                
            self.players[target]["alive"] = False
            print(f"\n{target}는(은) 밤중에 살해당했습니다.")
    
    def get_player_status(self):
        alive = {k:v["role"] for k, v in self.players.items() if v["alive"]}
        # alive = {k:v for k, v in self.players.items() if v["alive"]}  # DEBUG
        print(alive)
    
    def speak(self):
        """발언 생성 및 메시지 히스토리에 추가"""
        
        if self.current_speaker == "나":
            # 사용자 발언 입력 받기
            user_message = input(f"[나]: ")
            self.message_history.append(f"나: {user_message}")
        else:
            # TODO: SLLM으로 발언 생성
            prompt = load_prompt("prompts/civil_speak.yaml", encoding="utf-8")
            player = self.players[self.current_speaker]
            context = {
                "name": self.current_speaker,
                "role": player["role"],
                "reputation": player["reputation"],
                "message_history": list(self.message_history),
                "alive_players": [k for k,v in self.players.items() if v["alive"] and not self.current_speaker]
            }
            chain = prompt | self.sllm
            response = chain.invoke(context)
            # print("############### SPEAK 프롬프트######################")
            # print(prompt.invoke(context))

            ai_message = response.content
            print(f"[{self.current_speaker}]: {ai_message}")
            self.message_history.append(f"{self.current_speaker}: {ai_message}")
    
    def round(self, ridx):
        """라운드 진행"""
        print(f"\n{ridx}번째 아침이 밝았습니다.")
        
        # 토론
        speak_count = 0
        self.current_speaker = self.choice_next_speaker()

        while speak_count < self.limit_speak:
            if not self.current_speaker:
                break
            
            print(f"sidx {speak_count}", end=" ")
            self.speak()
            speak_count += 1
            self.current_speaker = self.choice_next_speaker()
            
        # 투표
        self.vote()
        self.get_player_status()  # DEBUG
        
        if self.check_game_over():
            self.is_game_over = True
            
            return
        
        # 밤
        print("\n밤이 되었습니다.")
        self.night_phase()
        self.is_game_over = self.check_game_over()
        self.get_player_status()  # DEBUG
        
        return
