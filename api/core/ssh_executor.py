import os
import asyncio
import asyncssh
import aiofiles
from datetime import datetime
from typing import Tuple, Optional

from api.config.settings import settings
from api.utils.logger import logger


class AsyncSSHExecutor:
    def __init__(self):
        self.host = settings.ssh_host
        self.port = settings.ssh_port
        self.username = settings.ssh_username
        self.password = settings.ssh_password

        self.connection: Optional[asyncssh.SSHClientConnection] = None
        self.command_timeout = 60.0
        self.audit_log_path = os.path.join(os.path.dirname(settings.log_file), "audit.log")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self) -> None:
        try:
            logger.info(f"Initiating SSH connection to {self.host}:{self.port}")
            self.connection = await asyncssh.connect(
                self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                known_hosts=None
            )

            logger.info("SSH connection established successfully")
        except Exception as error:
            logger.critical(f"SSH Connection failed: {error}")
            raise ConnectionError(f"Could not connect to isolated environment: {error}")

    async def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            await self.connection.wait_closed()
            logger.info("SSH connection closed")

    async def _log_audit(self, command: str, input_data: str, stdout: str, stderr: str, exit_code: int):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (
            f"[{timestamp}] CMD: {command}\n"
            f"IN: {input_data[:50]}...\n"
            f"OUT: {stdout[:100]}...\n"
            f"ERR: {stderr[:100]}...\n"
            f"CODE: {exit_code}\n"
            f"{'=' * 50}\n"
        )
        try:
            async with aiofiles.open(self.audit_log_path, mode="a", encoding="utf-8") as f:
                await f.write(entry)
        except Exception as error:
            logger.warning(f"Failed to write audit log: {error}")

    async def execute_command(self, command: str, input_data: Optional[str] = None) -> Tuple[int, str, str]:
        if not self.connection:
            await self.connect()

        try:
            logger.info(f"Executing: {command}")

            if input_data and not input_data.endswith("\n"):
                input_data += "\n"

            process = await asyncio.wait_for(
                self.connection.run(command, input=input_data, check=False),
                timeout=self.command_timeout
            )

            stdout = str(process.stdout).strip() if process.stdout else ""
            stderr = str(process.stderr).strip() if process.stderr else ""

            await self._log_audit(command, input_data or "", stdout, stderr, process.exit_status)

            return process.exit_status, stdout, stderr
        except asyncio.TimeoutError:
            logger.error(f"Command execution timed out: {command}")
            return 124, "", "Error: Command timed out"
        except Exception as error:
            logger.error(f"Execution failure: {error}")
            return 1, "", f"Error: {str(error)}"
