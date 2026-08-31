import anthropic

from . import config
from .tools import TOOLS, execute_tool


class Agent:
    def __init__(self, auto_confirm=False):
        self.client = anthropic.Anthropic()
        self.auto_confirm = auto_confirm

    def run_turn(self, messages):
        """Runs one user turn to completion, handling tool calls and paused
        turns. Mutates `messages` in place and returns (messages, reply_text)."""
        while True:
            response = self.client.messages.create(
                model=config.MODEL,
                max_tokens=config.MAX_TOKENS,
                system=config.SYSTEM_PROMPT,
                tools=TOOLS,
                output_config={"effort": config.EFFORT},
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = execute_tool(
                            block.name, block.input, self.auto_confirm
                        )
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result,
                            }
                        )
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
                continue

            if response.stop_reason == "pause_turn":
                continue

            if response.stop_reason == "refusal":
                return messages, "[Moni hat die Anfrage abgelehnt.]"

            text = "".join(b.text for b in response.content if b.type == "text")
            return messages, text
