"""ForgeLLM Public Hugging Face ZeroGPU Demo.

Interactive Gradio 5.x chat demonstration powered by ForgeLLM's inference engine.
"""

import os
import sys

# Ensure local imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr
from adapter import ZeroGPUInferenceEngine

# Initialize inference engine instance and load model weights eagerly
engine = ZeroGPUInferenceEngine()
engine.load_model()

DEFAULT_SYSTEM_PROMPT = (
    "You are ForgeLLM, an enterprise-grade AI assistant specialized in LLMOps, "
    "fine-tuning pipelines, model evaluation, and production inference."
)


def chat_response(
    message: str,
    history: list[dict[str, str] | list[str]],
    system_prompt: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
):
    """Handle chat generation and yield streaming responses with telemetry."""
    if not message or not message.strip():
        yield "", "⚠️ Please enter a valid prompt."
        return

    # Build ChatML formatted message array
    messages = []
    if system_prompt and system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})

    # Process conversation history (handles both Gradio 4 format and Gradio 5 format)
    if history:
        for turn in history:
            if isinstance(turn, dict):
                messages.append(turn)
            elif isinstance(turn, (list, tuple)) and len(turn) == 2:
                user_msg, bot_msg = turn
                if user_msg:
                    messages.append({"role": "user", "content": str(user_msg)})
                if bot_msg:
                    messages.append({"role": "assistant", "content": str(bot_msg)})

    messages.append({"role": "user", "content": message.strip()})

    telemetry_summary = "Initializing generation..."
    for chunk_text, telemetry in engine.generate_stream(
        messages=messages,
        max_new_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
    ):
        if telemetry:
            telemetry_summary = (
                f"⚡ **Speed:** `{telemetry.get('tokens_per_sec', 0.0)} tok/s` | "
                f"⏱️ **Latency:** `{telemetry.get('latency_sec', 0.0)}s` | "
                f"🚀 **TTFT:** `{telemetry.get('ttft_sec', 0.0)}s` | "
                f"📊 **Tokens:** `{telemetry.get('tokens_generated', 0)}` | "
                f"🖥️ **Device:** `{telemetry.get('device', 'unknown')}`"
            )
        yield chunk_text, telemetry_summary


try:
    import spaces

    gpu_decorator = spaces.GPU(duration=60)
except (ImportError, AttributeError):

    def gpu_decorator(func):
        return func


# Build Gradio ChatInterface
@gpu_decorator
def chat_fn(
    message: str,
    history: list[dict[str, str]],
    system_prompt: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
):
    """Streaming chat generator for Gradio ChatInterface."""
    if not message or not message.strip():
        yield "⚠️ Please enter a prompt."
        return

    # Build conversation messages
    messages = []
    if system_prompt and system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})

    for turn in history:
        if isinstance(turn, dict):
            messages.append(turn)
        elif isinstance(turn, (list, tuple)) and len(turn) == 2:
            messages.append({"role": "user", "content": str(turn[0])})
            messages.append({"role": "assistant", "content": str(turn[1])})

    messages.append({"role": "user", "content": message.strip()})

    for chunk_text, _telemetry in engine.generate_stream(
        messages=messages,
        max_new_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
    ):
        yield chunk_text


demo = gr.ChatInterface(
    fn=chat_fn,
    type="messages",
    title="⚒️ ForgeLLM — Enterprise LLM Platform Demo",
    description="Public Hugging Face ZeroGPU live inference powered by `Qwen/Qwen2.5-0.5B-Instruct`.",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="indigo"),
    additional_inputs=[
        gr.Textbox(
            label="System Prompt",
            value=DEFAULT_SYSTEM_PROMPT,
            lines=2,
        ),
        gr.Slider(
            label="Temperature",
            minimum=0.0,
            maximum=1.5,
            value=0.7,
            step=0.05,
            info="Creativity / randomness of generation",
        ),
        gr.Slider(
            label="Max New Tokens",
            minimum=32,
            maximum=512,
            value=256,
            step=32,
            info="Max tokens to generate",
        ),
        gr.Slider(
            label="Top-p",
            minimum=0.1,
            maximum=1.0,
            value=0.9,
            step=0.05,
            info="Nucleus sampling threshold",
        ),
    ],
    additional_inputs_accordion=gr.Accordion(
        label="⚙️ Generation Parameters & System Prompt", open=False
    ),
    examples=[
        ["Explain how LoRA fine-tuning works in ForgeLLM."],
        ["What is an OOM guardrail in GPU cluster orchestration?"],
        ["Compare Hugging Face Transformers vs vLLM serving latency."],
    ],
    cache_examples=False,
)

if __name__ == "__main__":
    engine.load_model()
    demo.launch(server_name="0.0.0.0", server_port=7860)
