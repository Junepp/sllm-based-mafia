import sys
import random
from collections import deque
import logging
import os
from datetime import datetime

from langchain_core.output_parsers import JsonOutputParser

from utils.sllm import get_sllm_instance
from utils.gemini import get_gemini_instance

from predefined_player.player import get_player
from prompt_template.template import get_template
from prompt_template.pydantic_structured_output import NextSpeaker, VoteResult, KillResult

class Game:
    def __init__(self,
                 num_player=5,
                 limit_speak=10,
                 message_window_size=15):
        
        # 로깅 설정
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG) # 모든 로그 레벨을 기록하도록 설정

        # 로그 파일 생성 및 핸들러 설정
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)  # logs 폴더 생성 (없으면)
        
        # 현재 시간으로 로그 파일명 생성
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"log_{current_time}.txt")
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG) # 파일에는 모든 레벨의 로그를 저장
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 콘솔 출력 핸들러 설정 (필터 추가)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO) # 콘솔에는 INFO 레벨 이상만 출력
        
        # 필터 생성: "player_thoughts" 메시지를 제외합니다.
        class NoPlayerThoughtsFilter(logging.Filter):
            def filter(self, record):
                return "player_thoughts" not in record.getMessage()
        
        console_handler.addFilter(NoPlayerThoughtsFilter())
        self.logger.addHandler(console_handler)

        
        # 게임 옵션
        self.user_name = input("이름을 입력하세요: ")
        self.num_player = num_player
        self.limit_speak = limit_speak
        self.message_window_size = message_window_size
        
        # 플레이어 초기화
        self.players = self.init_players()
        
        # 프롬프트 템플릿 뭉치 초기화
        self.prompt_templates = get_template()
        
        # # sllm 연결
        # self.sllm = get_sllm_instance()
        
        # sllm 연결
        self.sllm = get_gemini_instance()
        
        self.message_history = deque(maxlen=message_window_size)
        self.current_speaker = None
        
    def init_players(self):
        """게임 참가인원(CPC) 지정"""
        # 플레이어 지정
        players = get_player(num_player=self.num_player-1)
        players[self.user_name] = {}
        
        # 마피아/시민 역할 분배
        num_mafia = max(1, self.num_player // 3)
        mafia_players = random.sample(players.keys(), num_mafia)
        
        for name in players.keys():
            players[name]["alive"] = True
            players[name]["role"] = "마피아" if name in mafia_players else "시민"
            players[name]["type"] = "user" if name == self.user_name else "cpc"

        self.logger.info(f"나 {self.user_name}은(는) {players[self.user_name]['role']}이다!")
        
        return players
    
    def check_game_over(self):
        """게임 종료 조건 체크"""
        alive_mafia = len([1 for _, info in self.players.items() if info["role"] == "마피아" and info["alive"]])
        alive_civil = len([1 for _, info in self.players.items() if info["role"] == "시민" and info["alive"]])
        
        if alive_mafia == 0:
            self.logger.info("시민 승리!")
            return True
        
        if alive_mafia >= alive_civil:
            self.logger.info("마피아 승리!")
            return True
        
        return False
    
    def get_player_status(self):
        """딕셔너리 {플레이어 이름: 역할 (시민/마피아)} 출력"""
        alive = {k:v["role"] for k, v in self.players.items() if v["alive"]}  # 이름, 역할만
        # alive = {k:v for k, v in self.players.items() if v["alive"]}  # 모두 (디버깅용)
        self.logger.debug(f"현재 플레이어 상태: {alive}")
    
    # 1. 발언자 선정
    def choice_next_speaker(self, previous_speaker):
        """다음 발언자 CPC중에서 선택 (SLLM 활용)"""
        
        # 생존자 (유저와 이전발언자 제외)        
        alive_players = [name for name, info in self.players.items() 
                            if info["alive"] and name != previous_speaker and name != self.user_name]
        
        if not alive_players:
            return None

        prompt = self.prompt_templates["choose"]
        
        # structured output 적용
        output_parser = JsonOutputParser(pydantic_object=NextSpeaker)
        prompt = prompt.partial(format_instructions=output_parser.get_format_instructions())

        context = {
            "player_info": {name:{"reputation":self.players[name]["reputation"],
                                  "description":self.players[name]["description"]} for name in alive_players},
            "message_history": self.message_history,
        }

        chain = prompt | self.sllm | output_parser
        response = chain.invoke(context)
        next_speaker = response["next_speaker"]
        # print("####출력:", next_speaker)
        
        # 내부 생각 기록 (logger를 직접 사용)
        self.logger.debug(f"사회자의 다음 발언자 선정 결과: {response['next_speaker']}")
        self.logger.debug(f"사회자의 다음 발언자 선정 이유: {response['reason']}")
        
        # 현재 생존한 플레이어 중에 선택하도록 검증
        if next_speaker in alive_players :
            return next_speaker
        else:
            self.logger.warning(f"[ERR-choice] {next_speaker} not in alive player. random choose")
            return random.choice(alive_players)
    
    # 2. 발언    
    def cpc_speak(self):
        """CPC 발언 생성 및 메시지 히스토리에 추가"""
    
        player = self.players[self.current_speaker]
        prompt = self.prompt_templates["speak_civil"] if player["role"] == "시민" else self.prompt_templates["speak_mafia"]
        context = {
            "name": self.current_speaker,
            "role": player["role"],
            "reputation": player["reputation"],
            "message_history": list(self.message_history),
            "alive_players": [k for k,v in self.players.items() if v["alive"] and k != self.current_speaker]
        }
        chain = prompt | self.sllm
        response = chain.invoke(context)
        
        # 내부 생각 기록 (logger를 직접 사용)
        message_output = f"{self.current_speaker}: {response.content}"
        self.message_history.append(message_output)
        self.logger.info(message_output)
    
    # 3. 투표
    def vote(self):
        """투표 진행 (SLLM 활용)"""
        # 투표 집계
        votes = {}
        alive_players = [name for name, info in self.players.items() if info["alive"]]
        
        for player in alive_players:
            if player == self.user_name and self.players[player]["alive"]:
                target_candidates = [name for name, info in self.players.items() if info["alive"] and name != self.user_name]
                vote_target = input(f"{target_candidates}중 누구에게 투표하시겠습니까: ")
                if vote_target not in alive_players:
                    self.logger.warning(f"[WARN] {vote_target} not in alive player. random choose")
                    vote_target = random.choice(alive_players)
            
            else:
                prompt = self.prompt_templates["vote"] if self.players[player]["role"] == "시민" else self.prompt_templates["vote_mafia"]
                # structured output 적용
                output_parser = JsonOutputParser(pydantic_object=VoteResult)
                prompt = prompt.partial(format_instructions=output_parser.get_format_instructions())
                
                player_info = self.players[player]
                context = {
                    "name": player,
                    "role": player_info["role"],
                    "reputation": player_info["reputation"],
                    "description": player_info["description"],
                    "message_history": self.message_history,
                    "alive_players": alive_players
                }
                chain = prompt | self.sllm | output_parser
                response = chain.invoke(context)
                vote_target = response["vote_target"]
                
                if vote_target not in alive_players:
                    self.logger.warning(f"[WARN] {vote_target} not in alive player. random choose")
                    vote_target = random.choice(alive_players)
            
            self.logger.info(f"{player}는 {vote_target} 지목")
            self.logger.debug(f"{player}의 근거: {response['reason']}")
            
            votes[vote_target] = votes.get(vote_target, 0) + 1
        
        # 최다 득표자 처형
        max_votes = max(votes.values())
        executed = random.choice([p for p, v in votes.items() if v == max_votes])
        
        self.players[executed]["alive"] = False
        vote_result_msg = f"{executed}는(은) 투표로 처형되었습니다. 그의 정체는 {self.players[executed]['role']}"
        self.message_history.append(f"system: {vote_result_msg}")
        self.logger.info(vote_result_msg)
    
    # 4. 암살
    def night_phase(self):
        """밤 페이즈 - 마피아의 암살 (SLLM 활용)"""
        alive_mafia = [name for name, info in self.players.items() if info["role"] == "마피아" and info["alive"]]
        alive_civil = [name for name, info in self.players.items() if info["role"] == "시민" and info["alive"]]
        
        if not (alive_mafia and alive_civil):
            return
        
        targets = []
        for name_mafia in alive_mafia:
            # 유저가 마피아일때
            if name_mafia == self.user_name:
                target = input(f"{alive_civil} 중 누구를 암살하시겠습니까: ")
                if target not in alive_civil:
                    self.logger.warning(f"[ERR] {target} 은 잘못된 입력입니다. 다시 입력해주세요.")
                    target = input(f"{alive_civil} 중 누구를 암살하시겠습니까: ")
            
            else:
                prompt = self.prompt_templates["kill"]
                
                # structured output 적용
                output_parser = JsonOutputParser(pydantic_object=KillResult)
                prompt = prompt.partial(format_instructions=output_parser.get_format_instructions())
                
                context = {
                    "name": name_mafia,
                    "reputation": self.players[name_mafia]["reputation"],
                    "message_history": self.message_history,
                    "alive_civil": alive_civil
                }
                chain = prompt | self.sllm | output_parser
                response = chain.invoke(context)
                target = response["kill_target"]
                
                # 내부 생각 기록 (logger를 직접 사용)
                self.logger.debug(f"마피아 {name_mafia}는 살해 대상으로 {target} 선택")
                self.logger.debug(f"{name_mafia}의 선택 근거: {response['reason']}")

            targets.append(target)
        
        # print("암살 타겟리스트: ", targets)
        
        target = random.choice(targets)
        
        if target not in alive_civil:
            self.logger.warning(f"[WARN] {target} not in civil. random choose")
            target = random.choice(alive_civil)
            
        self.players[target]["alive"] = False
        kill_msg = f"{target}는(은) 밤중에 살해당했습니다. 그의 정체는 {self.players[target]['role']}"
        self.message_history.append(f"system: {kill_msg}")
        self.logger.info(kill_msg)
    
    def round(self, ridx):
        """라운드 진행"""
        self.logger.info(f"{ridx}번째 아침이 밝았습니다.")
        
        # 사회자의 진행
        num_alive_mafia = len([1 for _, info in self.players.items() if info["role"] == "마피아" and info["alive"]])
        info = f"system: 남은 마피아는 {num_alive_mafia}명입니다."
        self.logger.info(info)
        self.message_history.append(info)
        
        # 토론
        speak_count = 0
        self.current_speaker = None 

        while speak_count < self.limit_speak:           
            # 유저가 살아있고, 지난턴에 발언하지 않았을때만
            if self.players[self.user_name]["alive"] and self.current_speaker != self.user_name:
                user_input = input(f"{self.user_name}: ")
                
                # 유저 발언시
                if user_input:
                    self.current_speaker = self.user_name
                    my_message = f"{self.user_name}: {user_input}"
                    self.message_history.append(my_message)
                    self.logger.debug(my_message)
                
                else:
                    self.current_speaker = self.choice_next_speaker(previous_speaker=self.current_speaker)
                    self.cpc_speak()
                    
            # 발언자 선정
            else:
                self.current_speaker = self.choice_next_speaker(previous_speaker=self.current_speaker)
                self.cpc_speak()

            speak_count += 1
        
        self.logger.info("발언 끝, 투표 시작")
        
        # 투표
        self.vote()
        self.get_player_status()  # DEBUG
        
        # 게임 종료 체크 (투표후)
        if self.check_game_over():           
            return True
        
        # 밤
        self.logger.info("밤이 되었습니다.")
        self.night_phase()
        
        # 게임 종료 체크 (암살후)
        if self.check_game_over():
            return True
        
        self.get_player_status()  # DEBUG
        
        return False
