import random
from collections import deque

from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser

from utils.sllm import get_sllm_instance
from utils.gemini import get_gemini_instance

from predefined_player.player import get_player
from prompt_template.template import get_template


class Game:
    def __init__(self,
                 sllm_name,
                 sllm_endpoint,
                 num_player=5,
                 limit_speak=10,
                 message_window_size=10):
        
        # 게임 옵션
        self.user_name = input("이름을 입력하세요: ")
        self.num_player = num_player
        self.limit_speak = limit_speak
        self.message_window_size = message_window_size
        
        # 플레이어 초기화
        self.players = self.init_players()
        
        # 프롬프트 템플릿 뭉치 초기화
        self.prompt_templates = get_template()
        
        # sllm 연결
        # self.sllm = get_sllm_instance(
        #     model_name=sllm_name,
        #     model_endpoint=sllm_endpoint
        # )
        
        # sllm 연결
        self.sllm = get_gemini_instance()
        
        self.message_history = deque(maxlen=message_window_size)
        self.is_game_over = False
        self.current_speaker = None
        
    def init_players(self):
        """게임 참가인원 생성"""
        # 플레이어 지정
        players = get_player(num_player=self.num_player-1)
        players[self.user_name] = {}
        
        # 마피아/시민 역할 분배
        num_mafia = max(1, self.num_player // 3)
        mafia_players = random.sample(players.keys(), num_mafia)
        
        for name in players.keys():
            players[name]["alive"] = True
            players[name]["role"] = "마피아" if name in mafia_players else "시민" # role 한글로 변경
            players[name]["type"] = "user" if name == self.user_name else "cpc"

        print(f"나 {self.user_name}은(는) {players[self.user_name]['role']} 이다!")
        
        return players
    
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
    
    def get_player_status(self):
        alive = {k:v["role"] for k, v in self.players.items() if v["alive"]}  # 이름, 역할만
        # alive = {k:v for k, v in self.players.items() if v["alive"]}  # 모두 (DEBUG)
        print(alive)
    
    # 1. 발언자 선정
    class NextSpeaker(BaseModel):
        """다음 발언자 선정 모델"""
        next_speaker: str = Field(description="다음 발언자 이름")
        reason: str = Field(description="선정 이유")

    def choice_next_speaker(self, previous_speaker):
        """다음 발언자 선택 (SLLM 활용)"""
        
        # 생존자 (유저와 이전발언자 제외)        
        alive_players = [name for name, info in self.players.items() 
                            if info["alive"] and name != previous_speaker and name != self.user_name]
        
        if not alive_players:
            return None

        prompt = self.prompt_templates["choose"]
        
        # structured output 적용
        output_parser = JsonOutputParser(pydantic_object=self.NextSpeaker)
        prompt = prompt.partial(format_instructions=output_parser.get_format_instructions())

        context = {
            "player_info": {name:{"reputation":self.players[name]["reputation"],
                                  "description":self.players[name]["description"]} for name in alive_players},
            "message_history": self.message_history,
        }

        chain = prompt | self.sllm | output_parser
        response = chain.invoke(context)
        print(type(response), response)
        next_speaker = response["next_speaker"]
        # print("####출력:", next_speaker)

        # 현재 생존한 플레이어 중에 선택하도록 검증
        if next_speaker in alive_players:
            return next_speaker
        else:
            print(f"[ERR-choice] {next_speaker} not in alive player. random choose")
            return random.choice(alive_players)
    
    # 2. 발언    
    def speak(self):
        """발언 생성 및 메시지 히스토리에 추가"""
        
        if self.current_speaker == self.user_name:
            # 사용자 발언 입력 받기
            user_message = input(f"[{self.user_name}]: ")
            self.message_history.append(f"{self.user_name}: {user_message}")
        else:
            player = self.players[self.current_speaker]
            prompt = self.prompt_templates["speak_civil"] if player["role"] == "시민" else self.prompt_templates["speak_mafia"]
            context = {
                "name": self.current_speaker,
                "role": player["role"],
                "reputation": player["reputation"],
                "message_history": list(self.message_history),
                "alive_players": [k for k,v in self.players.items() if v["alive"] and not self.current_speaker]
            }
            chain = prompt | self.sllm
            response = chain.invoke(context)
            
            print("############### SPEAK 프롬프트######################")
            print(prompt.invoke(context))
            print("############### SPEAK 프롬프트######################")

            ai_message = response.content
            print(f"[{self.current_speaker}]: {ai_message}")
            self.message_history.append(f"{self.current_speaker}: {ai_message}")
    
    # 3. 투표
    class VoteResult(BaseModel):
        """투표 결과 모델"""
        vote_target: str = Field(description="투표 대상")

    def vote(self):
        """투표 진행 (SLLM 활용)"""
        # 투표 집계
        votes = {}
        alive_players = [name for name, info in self.players.items() 
                        if info["alive"]]
        
        for player in alive_players:
            if player == self.user_name:
                vote_target = input("누구에게 투표하시겠습니까? : ")
                if vote_target not in alive_players:
                    print(f"[WARN] {vote_target} not in alive player. random choose")
                    vote_target = random.choice(alive_players)
            else:
                prompt = self.prompt_templates["vote"]
                
                # structured output 적용
                output_parser = JsonOutputParser(pydantic_object=self.VoteResult)
                prompt = prompt.partial(format_instructions=output_parser.get_format_instructions())
                
                player_info = self.players[player]
                context = {
                    "name": player,
                    "role": player_info["role"],
                    "reputation": player_info["reputation"],
                    "message_history": self.message_history,
                    "alive_players": alive_players
                }
                chain = prompt | self.sllm | output_parser
                response = chain.invoke(context)
                vote_target = response["vote_target"]
                
                print(f"{player}: {vote_target} 지목")
                
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
    
    # 4. 암살
    class KillResult(BaseModel):
        """암살 결과 모델"""
        kill_target: str = Field(description="암살 대상")
        
    def night_phase(self):
        """밤 페이즈 - 마피아의 암살 (SLLM 활용)"""
        alive_mafia = [name for name, info in self.players.items() 
                      if info["role"] == "마피아" and info["alive"]]
        alive_civil = [name for name, info in self.players.items() 
                      if info["role"] == "시민" and info["alive"]]
        
        if alive_mafia and alive_civil:
            
            # TODO. mafia >= 2 구현
            # # 마피아가 2명 이상이면 서로 협의
            # if len(alive_mafia) >= 2:
            #     prompt = load_prompt("prompts/mafia_discussion.yaml", encoding="utf-8")
            #     context = {
            #         "mafia_names": alive_mafia,
            #         "message_history": self.message_history,
            #         "alive_civil": alive_civil
            #     }
            #     chain = prompt | self.sllm
            #     response = chain.invoke(context)
            #     print(f"[마피아협의]: {response.content}")

            target = random.choice(alive_civil)
            if self.user_name in alive_mafia:
                target = input("누구를 암살하시겠습니까?")
                if target not in alive_civil:
                    print("[ERR] 잘못된 입력입니다. 다시 입력해주세요.")
                    target = input("누구를 암살하시겠습니까? : ")
            else:
                prompt = self.prompt_templates["kill"]
                
                # structured output 적용
                output_parser = JsonOutputParser(pydantic_object=self.KillResult)
                prompt = prompt.partial(format_instructions=output_parser.get_format_instructions())
                
                mafia = alive_mafia[0]
                context = {
                    "mafia_name": mafia,
                    "message_history": self.message_history,
                    "alive_civil": alive_civil
                }
                chain = prompt | self.sllm | output_parser
                response = chain.invoke(context)
                target = response.kill_target
            
            if target not in alive_civil:
                print(f"[WARN] {target} not in civil. random choose")
                target = random.choice(alive_civil)
                
            self.players[target]["alive"] = False
            print(f"\n{target}는(은) 밤중에 살해당했습니다.")   
    
    def round(self, ridx):
        """라운드 진행"""
        print(f"\n{ridx}번째 아침이 밝았습니다.")
        
        # 토론
        speak_count = 0
        self.current_speaker = None 

        while speak_count < self.limit_speak:           
            
            user_input = input(f"[{self.user_name}]: ") if self.current_speaker != self.user_name else False
            print(f"\r")
            
            # 유저 발언시
            if user_input:
                self.current_speaker = self.user_name
                my_message = f"[{self.user_name}]: {user_input}"
                
                print(my_message)
                self.message_history.append(my_message)
                
            # 발언자 선정
            else:
                self.current_speaker = self.choice_next_speaker(previous_speaker=self.current_speaker)
                self.speak()

            speak_count += 1
        
        print("발언 끝, 투표 시작")
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
