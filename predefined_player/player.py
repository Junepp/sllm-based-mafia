"""
player.json: GPT-4o generated player persona

stat
    logic (논리력): 논리적으로 사고하고 분석하는 능력
    intuition (직감력): 사람의 감정과 분위기를 읽고 판단하는 능력
    trustworthiness (신뢰도): 다른 플레이어가 신뢰하는 정도
    social_influence (사회적 영향력): 대화를 주도하거나 분위기를 조정하는 능력
    adaptability (적응력): 게임의 흐름에 맞춰 자신의 태도를 바꾸는 능력
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
