from langchain_core.prompts import load_prompt


def get_template():
    template_dir_path = "prompt_template"

    prompt_template = {}
    
    prompt_template["choose"] = load_prompt(f"{template_dir_path}/choose_next_speaker.yaml", encoding="utf-8")
    prompt_template["speak_civil"] = load_prompt(f"{template_dir_path}/speak_civil.yaml", encoding="utf-8")
    prompt_template["speak_mafia"] = load_prompt(f"{template_dir_path}/speak_mafia.yaml", encoding="utf-8")
    prompt_template["vote"] = load_prompt(f"{template_dir_path}/vote_decision.yaml", encoding="utf-8")
    prompt_template["kill"] = load_prompt(f"{template_dir_path}/mafia_kill_decision.yaml", encoding="utf-8")
    
    return prompt_template


if __name__ == "__main__":
    templates = get_template()
    for k, v in templates.items():
        print(f"prompt {k} // {v}")
        print("="*30)
    