from typing import Any, Literal

import tomli
import tomli_w
from amrita_core import set_config
from amrita_core.config import (
    AmritaConfig,
    BaseModel,
    FunctionConfig,
    LLMConfig,
)
from pydantic import Field

from .constants import (
    CONFIG_DIR,
    CONFIG_PATH,
    COOKIE_CONFIG,
    MEMORY_SESSIONS_DIR,
    PRESETS_DIR,
)


class ModelConfig(BaseModel):
    """Model configuration"""

    top_k: int = Field(
        default=50,
        description="TopK (Some model adapters may not support this parameter)",
    )
    top_p: float = Field(default=0.8, description="@ui[slider,0,1]TopP")
    temperature: float = Field(default=0.6, description="@ui[slider,0,1]Temperature")
    stream: bool = Field(
        default=False,
        description="Whether to enable streaming response (output by character)",
    )
    multimodal: bool = Field(
        default=False,
        description="Whether to support multimodal input (e.g. image recognition)",
    )


class AgentConfig(BaseModel):
    use_minimal_context: bool = Field(
        default=True,
        description="Whether to use minimal context, i.e. system prompt + user's last message (disabling this option will use all context from the message list, which may consume a large amount of Tokens during Agent workflow execution; enabling this option may effectively reduce token usage)",
    )

    tool_calling_mode: Literal["agent", "rag", "none"] = Field(
        default="agent",
        description="Tool calling mode, i.e. whether to use Agent or RAG to call tools",
    )
    agent_tool_call_limit: int = Field(
        default=20, description="Tool call limit in agent mode"
    )
    agent_tool_call_notice: Literal["hide", "notify"] = Field(
        default="hide",
        description="Method of showing tool call status in agent mode, hide to conceal, notify to inform",
    )
    agent_thought_mode: Literal[
        "reasoning", "chat", "reasoning-required", "reasoning-optional"
    ] = Field(
        default="reasoning",
        description="Thinking mode in agent mode, reasoning mode will first perform reasoning process, then execute tasks; "
        "reasoning-required requires task analysis for each Tool Calling; "
        "reasoning-optional does not require reasoning but allows it; "
        "chat mode executes tasks directly",
    )
    agent_reasoning_hide: bool = Field(
        default=False, description="Whether to hide the thought process in agent mode"
    )
    agent_middle_message: bool = Field(
        default=True,
        description="Whether to allow Agent to send intermediate messages to users in agent mode",
    )
    agent_mcp_client_enable: bool = Field(
        default=False, description="Whether to enable MCP client"
    )
    agent_mcp_server_scripts: list[str] = Field(
        default_factory=list, description="List of MCP server scripts"
    )
    require_tools: bool = Field(
        default=False,
        description="Whether to force at least one tool to be used per call",
    )
    memory_length_limit: int = Field(
        default=50, description="Maximum number of messages in memory context"
    )
    max_tokens: int = Field(
        default=100,
        description="Maximum number of tokens generated in a single response",
    )
    tokens_count_mode: Literal["word", "bpe", "char"] = Field(
        default="bpe",
        description="Token counting mode: bpe(subwords)/word(words)/char(characters)",
    )
    enable_tokens_limit: bool = Field(
        default=True, description="Whether to enable context length limits"
    )
    session_tokens_windows: int = Field(
        default=5000, description="Session tokens window size"
    )
    llm_timeout: int = Field(
        default=60, description="API request timeout duration (seconds)"
    )
    enable_memory_abstract: bool = Field(
        default=True,
        description="Whether to enable context memory summarization (will delete context and insert a summary into system instruction)",
    )
    memory_abstract_proportion: float = Field(
        default=15e-2,
        description="@ui[slider,0,1] Context summarization proportion (0.15=15%)",
    )
    enable_multi_modal: bool = Field(
        default=True,
        description="Whether to enable multi-modal support (currently only supports image)",
    )


_config: AgentConfig | None = None


# PLUGINS_DIR = CWD/"plugins"
def init_dir():
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def init_config():
    global _config
    init_dir()
    if not CONFIG_PATH.exists():
        _config = AgentConfig()
        with open(CONFIG_PATH, "w", encoding="u8") as f:
            f.write(tomli_w.dumps(_config.model_dump()))
    if _config is None:
        with open(CONFIG_PATH, "rb") as f:
            _config = AgentConfig.model_validate(tomli.load(f))


def get_config() -> AgentConfig:
    global _config
    init_config()
    assert _config is not None
    return _config


def reload_config():
    global _config
    _config = None
    init_config()


def apply_config():
    config: AgentConfig = get_config()
    func_conf = FunctionConfig.model_validate(config, from_attributes=True)
    llm_conf = LLMConfig.model_validate(config, from_attributes=True)
    core_conf = AmritaConfig(
        function_config=func_conf, llm=llm_conf, cookie=COOKIE_CONFIG
    )
    set_config(core_conf)

def update_config(config: AgentConfig):
    with open(CONFIG_PATH, "w", encoding="u8") as f:
        f.write(tomli_w.dumps(config.model_dump()))
    reload_config()
    apply_config()