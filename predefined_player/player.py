"""
player.json: GPT-4o generated player persona

"""

import json
import random

    
def get_player(num_player):
    with open("predefined_player/players.json", "r", encoding="utf-8") as file:
        players = json.load(file)
    
    candidates = list(players.keys())
    members_name = random.sample(candidates, num_player)
    members = {name:players[name] for name in members_name}
    
    return members

if __name__ == "__main__":
    players = get_player(num_player=5)
    print(type(players), len(players))
    print(players)
