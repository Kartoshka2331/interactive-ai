from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    server_host: str = "0.0.0.0"
    server_port: int = 8888
    debug_mode: bool = False

    openrouter_api_key: str
    openrouter_model: str = "google/gemini-3-flash-preview"
    max_agent_steps: int = 25

    ssh_host: str = "127.0.0.1"
    ssh_port: int = 2222
    ssh_username: str = "root"
    ssh_password: str

    host_shared_data_path: str = "./shared_data"
    container_shared_data_path: str = "/root/data"

    log_level: str = "INFO"
    log_file: str = "logs/interactive_ai.log"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
