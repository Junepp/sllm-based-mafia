import yaml
from box import Box
from game import Game

def game():
    with open("config.yaml", "r") as f:
        config_yaml = yaml.load(f, Loader=yaml.FullLoader)
        config = Box(config_yaml)
    
    # 게임 세팅 (사용자 입력)
    num_player = 5
    limit_speak = 10
    
    print("============game start============")
    
    # 게임 초기화
    game = Game(
        sllm_name=config.sllm_model,
        sllm_endpoint=config.sllm_endpoint,
        num_player=num_player,
        limit_speak=limit_speak
    )
    
    # 게임 진행
    turn_idx = 1
    game.get_player_status()  # DEBUG
    
    while not game.is_game_over:
        game.round(turn_idx)
        
        input(f"{turn_idx}라운드가 끝. 계속하려면 enter")
        turn_idx += 1
    
if __name__ == "__main__":
    game()
    