from game import Game

def game():   
    # 게임 세팅 (사용자 입력)
    num_player = 5
    limit_speak = 10
    
    # 게임 초기화
    game = Game(
        num_player=num_player,
        limit_speak=limit_speak
    )
    turn_idx = 1
        
    game.logger.info("============game start============")
    game.get_player_status()  # DEBUG
    
    is_gameover = False
    while not is_gameover:
        is_gameover = game.round(turn_idx)
        
        if is_gameover:
            game.logger.info("게임이 종료되었습니다")
            break
        
        else:
            game.logger.info(f"{turn_idx}라운드 끝")
            input(f"{turn_idx}라운드 끝. 계속하려면 enter")
        
        turn_idx += 1
    
if __name__ == "__main__":
    game()
    