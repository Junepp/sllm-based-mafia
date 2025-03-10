import yaml
from box import Box
from predefined_player.player import get_player

def game():
    with open("config.yaml", "r") as f:
        config_yaml = yaml.load(f, Loader=yaml.FullLoader)
        config = Box(config_yaml)
    
    print("============game start============")
    
    # =========================================
    # 입력 (게임 세팅)

    # 플레이어 수 입력 (자신 포함)
    num_player = 4
    players = get_player(num_player=num_player)
    print("참가자:", players)

    # 턴당 발언 횟수 조정
    limit_speak = 20
    
    # 직업 종류, 인원 조정
    
    # =========================================
    
    # 역할 지정
    mafia = ...
    civil = ...
    
    # =========================================
    # 게임 시작
    
    turn_idx = 1
    while True:
        print(f"\n{turn_idx}번째 아침이 밝았습니다. 자유롭게 토론해주세요")
        
        count_speak = 0
        while count_speak < 20 and ...:
            ...

        turn_idx += 1
        break
    
    
if __name__ == "__main__":
    game()