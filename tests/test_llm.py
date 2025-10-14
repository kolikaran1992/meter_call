import pytest
from meter_call import LLMFallbackCaller
from meter_call.omniconfig import logger, config
import os
from pathlib import Path
from litellm.types.utils import ModelResponse


secrets_dir = os.environ.get("SECRETS_DIRECTORY") or ""
print(secrets_dir, "settings_dir")
if secrets_dir:
    # update config with llm api keys
    config = config.from_env(
        "default",
        keep=True,
        SETTINGS_FILE_FOR_DYNACONF=list(Path(secrets_dir).rglob("*.toml")),
    )

# -------------------
# Prepare providers #
# -------------------

providers_list = [
    [
        {"model": "mistral/mistral-tiny", "api_key": config.llm_api_key.mistral},
    ]
]

# ---------------------------
# Fixed input message
# ---------------------------
messages = [{"role": "user", "content": "tell me hi in 5 words"}]


# ---------------------------
# Fixture parametrized with multiple provider lists
# ---------------------------
@pytest.fixture(params=providers_list)
def llm_caller(request):
    return LLMFallbackCaller(providers=request.param, config=config)


# ---------------------------
# Test synchronous call
# ---------------------------
def test_llm_call(llm_caller):
    result = llm_caller.call(messages=messages)
    assert isinstance(result, ModelResponse)
    provider_names = [p["model"] for p in llm_caller.providers]
    logger.info(f"Providers {provider_names} returned: {result}")


# ---------------------------
# Test asynchronous call
# ---------------------------
@pytest.mark.asyncio
async def test_llm_acall(llm_caller):
    result = await llm_caller.acall(messages=messages)
    assert isinstance(result, ModelResponse)
    provider_names = [p["model"] for p in llm_caller.providers]
    logger.info(f"Providers {provider_names} returned: {result}")
