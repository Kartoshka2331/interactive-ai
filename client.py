import asyncio
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

import httpx
import questionary
from questionary import Choice
from prompt_toolkit.history import FileHistory
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text
from rich.theme import Theme
from rich.table import Table


API_URL = "http://localhost:8888/v1/chat/completions"
HISTORY_FILE = Path("chat_history.json")
CONFIG_FILE = Path("client_config.json")
CMD_HISTORY_FILE = ".cmd_history"


COLOR_PRIMARY = "#00BFFF"
COLOR_ACCENT = "#FF00FF"
COLOR_USER_BORDER = "#1E90FF"
COLOR_AI_BORDER = "#00BFFF"
COLOR_CMD_EXEC = "#00FF7F"
COLOR_CMD_RESULT = "#FFA500"
COLOR_CMD_BG = "#101010"

console = Console(theme=Theme({
    "primary": f"bold {COLOR_PRIMARY}",
    "accent": f"bold {COLOR_ACCENT}",
    "text.main": "#FFFFFF",
    "text.dim": "dim #B0C4DE",
    "user.header": f"bold {COLOR_PRIMARY}",
    "user.text": "#E0FFFF",
    "ai.header": "bold #FFFFFF",
    "ai.text": "#FFFFFF",
    "cmd.exec.text": "bold #FFFFFF",
    "cmd.result.text": "#FFD700",
}))


class ConfigurationManager:
    def __init__(self):
        self.default_config = {
            "model": "google/gemini-3-flash-preview",
            "show_command_output": True,
            "max_history": 50
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as file:
                    return {**self.default_config, **json.load(file)}
            except Exception:
                return self.default_config
        return self.default_config

    def save_config(self):
        with open(CONFIG_FILE, "w") as file:
            json.dump(self.config, file, indent=4)

    def update(self, key: str, value: Any):
        self.config[key] = value
        self.save_config()


class HistoryManager:
    def __init__(self):
        self.history: List[Dict[str, str]] = []

    def load_history(self):
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r") as file:
                    self.history = json.load(file)
            except Exception:
                self.history = []

    def save_history(self):
        with open(HISTORY_FILE, "w") as file:
            json.dump(self.history, file, indent=4)

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        self.save_history()

    def clear(self):
        self.history = []
        self.save_history()


class InteractiveAIClient:
    def __init__(self):
        self.config_manager = ConfigurationManager()
        self.history_manager = HistoryManager()
        self.history_manager.load_history()
        self.client = httpx.AsyncClient(timeout=120.0)
        self.input_history = FileHistory(CMD_HISTORY_FILE)

    @staticmethod
    def _hard_clear():
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def _remove_input_line():
        sys.stdout.write("\033[1A\033[2K")
        sys.stdout.flush()

    @staticmethod
    def _print_exec_panel(content: str, width: int):
        cmd_content = Text(content, style="cmd.exec.text")
        console.print(
            Panel(
                cmd_content,
                title=f"[bold {COLOR_CMD_EXEC}]>>> EXEC[/]",
                title_align="left",
                border_style=COLOR_CMD_EXEC,
                width=width,
                padding=(0, 1),
                style=f"on {COLOR_CMD_BG}"
            )
        )

    @staticmethod
    def _print_result_panel(content: str, width: int):
        out_content = Text(content, style="cmd.result.text")
        console.print(
            Panel(
                out_content,
                title=f"[bold {COLOR_CMD_RESULT}]↳ RESULT[/]",
                title_align="left",
                border_style=COLOR_CMD_RESULT,
                width=width,
                padding=(0, 1),
                style=f"on {COLOR_CMD_BG}"
            )
        )

    async def start(self):
        while True:
            self._hard_clear()
            self._print_header()

            menu_style = questionary.Style([
                ("qmark", f"fg:{COLOR_PRIMARY} bold"),
                ("question", "fg:#FFFFFF bold"),
                ("answer", f"fg:{COLOR_PRIMARY} bold"),
                ("pointer", f"fg:{COLOR_ACCENT} bold"),
                ("highlighted", f"fg:{COLOR_PRIMARY} bold"),
                ("selected", "fg:#FFFFFF"),
            ])

            try:
                choice = await questionary.select(
                    "MAIN MENU",
                    choices=[
                        Choice("Chat"),
                        Choice("Settings"),
                        Choice("Clear History"),
                        Choice("Exit")
                    ],
                    style=menu_style,
                    qmark="◈"
                ).ask_async(kbi_msg="")

                if choice is None or choice == "Exit":
                    await self._shutdown()

                if choice == "Chat":
                    await self._chat_session()
                elif choice == "Settings":
                    await self._settings_menu()
                elif choice == "Clear History":
                    self.history_manager.clear()
                    console.print("[bold green]History cleared[/bold green]")
                    await asyncio.sleep(0.4)
            except KeyboardInterrupt:
                await self._shutdown()
                break

    async def _shutdown(self):
        try:
            await self.client.aclose()
        except Exception:
            pass
        sys.exit(0)

    @staticmethod
    def _print_header():
        grid = Table.grid(expand=True)
        grid.add_column(justify="center")

        main_title = Text("I N T E R A C T I V E  A I", style="bold white")
        subtitle = Text("Created by ", style="text.dim")
        subtitle.append("Kartoshka2331", style="accent")
        subtitle.append(" | v1.1", style="text.dim")

        panel = Panel(
            Align.center(Group(main_title, subtitle)),
            border_style=COLOR_PRIMARY,
            padding=(0, 2),
            width=60
        )
        console.print(Align.center(panel))
        console.print()

    async def _settings_menu(self):
        while True:
            self._hard_clear()
            self._print_header()
            config = self.config_manager.config

            style = questionary.Style([
                ("question", f"fg:{COLOR_PRIMARY} bold"),
                ("pointer", f"fg:{COLOR_ACCENT} bold"),
                ("highlighted", f"fg:{COLOR_PRIMARY} bold"),
            ])

            try:
                choice = await questionary.select(
                    "SETTINGS",
                    choices=[
                        f"Model: {config["model"]}",
                        f"Show Command Output: {"ON" if config["show_command_output"] else "OFF"}",
                        "Back"
                    ],
                    style=style,
                    qmark="⚙️"
                ).ask_async()

                if choice == "Back" or choice is None:
                    break
                elif choice.startswith("Model"):
                    new_model = await questionary.text("Enter model name:", default=config["model"]).ask_async()
                    if new_model:
                        self.config_manager.update("model", new_model)
                elif choice.startswith("Show Command Output"):
                    self.config_manager.update("show_command_output", not config["show_command_output"])
            except KeyboardInterrupt:
                break

    def _render_message(self, role: str, content: str):
        width = console.size.width
        max_panel_width = int(width * 0.8)

        if role == "user":
            panel = Panel(
                Text(content, style="user.text"),
                title="[user.header]User[/user.header]",
                title_align="right",
                border_style=COLOR_USER_BORDER,
                padding=(0, 1),
                width=min(len(content) + 4, max_panel_width)
            )
            console.print(Align.right(panel))
        elif role == "assistant":
            panel = Panel(
                Markdown(content),
                title="[ai.header]Interactive AI[/ai.header]",
                title_align="left",
                border_style=COLOR_AI_BORDER,
                padding=(0, 1),
                width=max_panel_width
            )
            console.print(Align.left(panel))

        elif role == "tool_exec" and self.config_manager.config["show_command_output"]:
            self._print_exec_panel(content, max_panel_width)
        elif role == "tool_result" and self.config_manager.config["show_command_output"]:
            self._print_result_panel(content, max_panel_width)

        if role in ["user", "assistant"]:
            console.print()

    async def _chat_session(self):
        self._hard_clear()

        if self.history_manager.history:
            for message in self.history_manager.history:
                self._render_message(message["role"], message["content"])

        console.print(Panel(Align.center("[text.dim]Use ↑/↓ for history. Ctrl+C to exit.[/text.dim]"), border_style=COLOR_CMD_BG))

        while True:
            try:
                user_input = await questionary.text(
                    "",
                    qmark=">",
                    history=self.input_history,
                    style=questionary.Style([("qmark", f"fg:{COLOR_PRIMARY} bold")])
                ).ask_async()

                if user_input is None:
                    break

                self._remove_input_line()

                if not user_input.strip():
                    continue

                if user_input.strip().lower() in ["exit", "quit"]:
                    break

                self._render_message("user", user_input)
                self.history_manager.add_message("user", user_input)

                payload = {
                    "model": self.config_manager.config["model"],
                    "messages": [message for message in self.history_manager.history if message["role"] in ["user", "assistant"]],
                    "stream": True
                }

                await self._handle_streaming_response(payload)
            except KeyboardInterrupt:
                break
            except Exception as error:
                console.print(f"\n[danger]Error: {str(error)}[/danger]")

    async def _handle_streaming_response(self, payload: Dict):
        full_response_text = ""
        width = console.size.width
        max_panel_width = int(width * 0.8)

        with Live(Spinner("dots", text="Processing...", style="primary"), refresh_per_second=12, auto_refresh=True, transient=True) as live_display:
            try:
                async with self.client.stream("POST", API_URL, json=payload) as response:
                    if response.status_code != 200:
                        live_display.stop()
                        console.print(Panel(f"[danger]API Error {response.status_code}[/danger]", border_style="danger"))
                        return

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue

                        data_str = line.replace("data: ", "").strip()
                        if data_str == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content_chunk = delta.get("content")

                            if content_chunk:
                                full_response_text += content_chunk
                                live_panel = Panel(
                                    Markdown(full_response_text),
                                    title="[ai.header]Interactive AI[/ai.header]",
                                    title_align="left",
                                    border_style=COLOR_AI_BORDER,
                                    width=max_panel_width,
                                    padding=(0, 1)
                                )
                                live_display.update(Align.left(live_panel))

                            raw_cmd_output = delta.get("command_output")
                            if raw_cmd_output and self.config_manager.config["show_command_output"]:
                                clean_output = raw_cmd_output.strip()

                                live_display.stop()

                                if clean_output.startswith("> "):
                                    cmd_text = clean_output[2:]
                                    self._print_exec_panel(cmd_text, max_panel_width)
                                    self.history_manager.add_message("tool_exec", cmd_text)
                                elif clean_output.startswith("< "):
                                    res_text = clean_output[2:]
                                    self._print_result_panel(res_text, max_panel_width)
                                    self.history_manager.add_message("tool_result", res_text)

                                live_display.start()

                                if full_response_text:
                                    live_display.update(Align.left(Panel(
                                        Markdown(full_response_text),
                                        title="[ai.header]Interactive AI[/ai.header]",
                                        title_align="left",
                                        border_style=COLOR_AI_BORDER,
                                        width=max_panel_width,
                                        padding=(0, 1)
                                    )))
                                else:
                                    live_display.update(Spinner("dots", text="Processing...", style="primary"))
                        except json.JSONDecodeError:
                            continue
            except (KeyboardInterrupt, asyncio.CancelledError):
                live_display.stop()
            except Exception as error:
                live_display.stop()
                console.print(Panel(f"[danger]Stream Error: {error}[/danger]", border_style="danger"))
                return

        if full_response_text:
            self.history_manager.add_message("assistant", full_response_text)

            final_panel = Panel(
                Markdown(full_response_text),
                title="[ai.header]Interactive AI[/ai.header]",
                title_align="left",
                border_style=COLOR_AI_BORDER,
                width=max_panel_width,
                padding=(0, 1)
            )
            console.print(Align.left(final_panel))
            console.print()


if __name__ == "__main__":
    client = InteractiveAIClient()

    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        sys.exit(0)
