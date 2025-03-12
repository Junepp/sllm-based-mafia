import yaml
from box import Box
from game import Game

def game():
    with open("config.yaml", "r") as f:
        config_yaml = yaml.load(f, Loader=yaml.FullLoader)
        config = Box(config_yaml)
    
    print("============game start============")
    
    # 게임 초기화
    game = Game(
        sllm_name=config.sllm_model,
        sllm_endpoint=config.sllm_endpoint,
        num_player=5,
        limit_speak=20
    )
    
    # 게임 진행
    turn_idx = 1
    while not game.is_game_over:
        game.round(turn_idx)
        turn_idx += 1
    
if __name__ == "__main__":
    game()