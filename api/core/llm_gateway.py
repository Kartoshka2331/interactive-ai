import json
import uuid
import time
from typing import List, AsyncGenerator, Any, Dict

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionToolParam

from api.config.settings import settings
from api.core.ssh_executor import AsyncSSHExecutor
from api.core.prompts import get_system_prompt
from api.utils.types import (
    ChatCompletionRequest,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
    Role
)
from api.utils.logger import logger


class LLMGateway:
    def __init__(self):
        self.client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.openrouter_api_key)
        self.default_model = settings.openrouter_model

        self.tools: List[ChatCompletionToolParam] = [
            {
                "type": "function",
                "function": {
                    "name": "execute_ssh_command",
                    "description": "Execute a shell command on the remote server. Supports stdin injection.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The bash command to execute (e.g., 'ls -la /root/data', 'python3 script.py')"
                            },
                            "input_data": {
                                "type": "string",
                                "description": "Optional stdin data (e.g., for interactive prompts or piping). Use \\n for newlines"
                            }
                        },
                        "required": ["command"]
                    }
                }
            }
        ]

    async def process_request(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_timestamp = int(time.time())

        messages = [{"role": "system", "content": get_system_prompt()}]
        messages.extend(request.messages)

        step_count = 0
        max_steps = settings.max_agent_steps

        async with AsyncSSHExecutor() as executor:
            while step_count < max_steps:
                logger.info(f"Processing agent step {step_count + 1}/{max_steps}")

                if max_steps - step_count <= 3:
                    messages.append({
                        "role": "system",
                        "content": f"WARNING: You have {max_steps - step_count} steps remaining. Wrap up your task immediately."
                    })

                current_tool_calls: Dict[int, Dict[str, Any]] = {}
                response_content = ""

                try:
                    stream = await self.client.chat.completions.create(
                        model=request.model or self.default_model,
                        messages=messages,
                        tools=self.tools,
                        tool_choice="auto",
                        stream=True,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        frequency_penalty=request.frequency_penalty,
                        presence_penalty=request.presence_penalty
                    )
                except Exception as error:
                    logger.error(f"OpenRouter API failed: {error}")
                    yield self._create_error_chunk(request_id, created_timestamp, str(error))
                    return

                async for chunk in stream:
                    if not chunk.choices:
                        continue

                    delta = chunk.choices[0].delta

                    if delta.content:
                        response_content += delta.content
                        yield self._create_chunk(request_id, created_timestamp, content=delta.content)

                    if delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            index = tool_call.index
                            if index not in current_tool_calls:
                                current_tool_calls[index] = {
                                    "id": tool_call.id,
                                    "function": {"name": "", "arguments": ""}
                                }
                            if tool_call.id:
                                current_tool_calls[index]["id"] = tool_call.id
                            if tool_call.function.name:
                                current_tool_calls[index]["function"]["name"] += tool_call.function.name
                            if tool_call.function.arguments:
                                current_tool_calls[index]["function"]["arguments"] += tool_call.function.arguments

                if not current_tool_calls:
                    logger.info("Agent decided to stop execution")
                    yield "[DONE]"
                    return

                messages.append({
                    "role": "assistant",
                    "content": response_content if response_content else None,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": tc["function"]
                        } for tc in current_tool_calls.values()
                    ]
                })

                for tc in current_tool_calls.values():
                    function_name = tc["function"]["name"]
                    arguments_str = tc["function"]["arguments"]
                    tool_call_id = tc["id"]

                    if function_name == "execute_ssh_command":
                        try:
                            args = json.loads(arguments_str)
                            command = args.get("command")
                            input_data = args.get("input_data")

                            yield self._create_chunk(
                                request_id,
                                created_timestamp,
                                command_output=f"> {command}"
                            )

                            exit_code, stdout, stderr = await executor.execute_command(command, input_data)

                            yield self._create_chunk(request_id, created_timestamp, command_output="< " + (stdout or stderr))

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": function_name,
                                "content": f"EXIT: {exit_code}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
                            })
                        except json.JSONDecodeError:
                            err_msg = "Error: Model generated invalid JSON arguments"
                            logger.warning(err_msg)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": function_name,
                                "content": err_msg
                            })
                        except Exception as error:
                            err_msg = f"Internal Execution Error: {str(error)}"
                            logger.error(err_msg)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": function_name,
                                "content": err_msg
                            })

                step_count += 1

            limit_msg = "\n[System: Execution limit reached. Halting process]"
            yield self._create_chunk(request_id, created_timestamp, content=limit_msg)
            yield "[DONE]"

    def _create_chunk(self, req_id: str, created: int, content: str = None, command_output: str = None) -> str:
        from api.api.v1.responses import create_sse_event

        delta = ChatCompletionChunkDelta(
            role=Role.ASSISTANT if content else None,
            content=content,
            command_output=command_output
        )

        chunk = ChatCompletionChunk(
            id=req_id, created=created, model=self.default_model,
            choices=[ChatCompletionChunkChoice(index=0, delta=delta)]
        )
        return create_sse_event(chunk)

    def _create_error_chunk(self, req_id: str, created: int, error_msg: str) -> str:
        from api.api.v1.responses import create_sse_event

        delta = ChatCompletionChunkDelta(content=f"\n**System Error**: {error_msg}")
        chunk = ChatCompletionChunk(
            id=req_id, created=created, model=self.default_model,
            choices=[ChatCompletionChunkChoice(index=0, delta=delta, finish_reason="stop")]
        )
        return create_sse_event(chunk)


llm_gateway = LLMGateway()
