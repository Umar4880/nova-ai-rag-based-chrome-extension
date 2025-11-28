from langchain_core.prompts import ChatPromptTemplate

from app.exceptions.server_error import PromptValidationError

import yaml
from pathlib import Path

class PromptTemplate:
    def __init__(self, file_path: str = None):
        if not file_path or len(file_path) == 0:
            self.file_path = Path(__file__).parent / "prompt.yaml"
        else:
            self.file_path = file_path

        self.all_prompts = self._load_prompts()

    def _load_prompts(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise PromptValidationError(message="YAML Error while parsing file", details={'original_exp':e})
        except Exception as e:
            raise PromptValidationError(message=f"Failed to load prompt from path:{self.file_path}", details={'original_exp':e})
        
    def build_template(self):
        try:
            # Access nested YAML structure: prompts.system_prompt
            system_prompt = self.all_prompts.get("prompts", {}).get("system_prompt", "")

            prompt_template = ChatPromptTemplate.from_messages([
                ("system", system_prompt+"\n\n**Relevant Context:**\n---\n{context}\n---"),
                ("human", "{input}")
            ])
            return prompt_template
        except Exception as e:
            raise PromptValidationError(message="Failed to create prompt template", details={'original_exp':e})