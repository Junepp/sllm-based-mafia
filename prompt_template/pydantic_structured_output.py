from pydantic import BaseModel, Field


class NextSpeaker(BaseModel):
    """다음 발언자 선정 모델"""
    next_speaker: str = Field(description="다음 발언자 이름")
    reason: str = Field(description="선정 이유")
    
class VoteResult(BaseModel):
    """투표 결과 모델"""
    vote_target: str = Field(description="투표 대상")
    reason: str = Field(description="투표 이유")
    
class KillResult(BaseModel):
    """암살 결과 모델"""
    kill_target: str = Field(description="암살 대상")
    reason: str = Field(description="암살 이유")
