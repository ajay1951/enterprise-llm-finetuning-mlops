"""ForgeLLM Public Hugging Face ZeroGPU Demo.

Interactive Gradio 5.x chat demonstration powered by ForgeLLM's inference engine.
"""

import os
import sys

# Ensure local imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr
from adapter import ZeroGPUInferenceEngine

# Initialize inference engine instance
engine = ZeroGPUInferenceEngine()

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


# Build Gradio UI
with gr.Blocks(
    title="ForgeLLM — Public ZeroGPU Demo",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="indigo"),
) as demo:
    gr.Markdown(
        """
        # ⚒️ ForgeLLM — Enterprise LLM Platform Demo
        ### Public Hugging Face ZeroGPU Inference Demonstration
        
        *Powered by ForgeLLM's streaming inference engine running `Qwen/Qwen2.5-0.5B-Instruct` on Hugging Face ZeroGPU.*
        """
    )

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Conversation",
                height=480,
                show_copy_button=True,
            )
            telemetry_box = gr.Markdown("Ready for generation.")

            with gr.Row():
                msg_input = gr.Textbox(
                    label="User Prompt",
                    placeholder="Ask ForgeLLM anything (e.g. 'Explain LoRA fine-tuning and PagedAttention')...",
                    lines=2,
                    scale=4,
                )
                submit_btn = gr.Button("Send 🚀", variant="primary", scale=1)

            clear_btn = gr.Button("Clear Conversation 🧹")

        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Generation Parameters")
            system_prompt_input = gr.Textbox(
                label="System Prompt",
                value=DEFAULT_SYSTEM_PROMPT,
                lines=3,
            )
            temperature_slider = gr.Slider(
                label="Temperature",
                minimum=0.0,
                maximum=1.5,
                value=0.7,
                step=0.05,
                info="Higher values produce more creative output, lower values are more deterministic.",
            )
            max_tokens_slider = gr.Slider(
                label="Max New Tokens",
                minimum=32,
                maximum=512,
                value=256,
                step=32,
                info="Maximum tokens to generate per response.",
            )
            top_p_slider = gr.Slider(
                label="Top-p (Nucleus Sampling)",
                minimum=0.1,
                maximum=1.0,
                value=0.9,
                step=0.05,
                info="Top cumulative probability mass for sampling.",
            )

            gr.Markdown(
                """
                ---
                **Architecture Notes:**
                - **ZeroGPU Demo Backend:** Native `TransformersBackend` with dynamic `@spaces.GPU` transient leasing.
                - **Production Serving Mode:** High-concurrency continuous batching via ForgeLLM `vLLMBackend`.
                - **GitHub Repo:** [ajay1951/enterprise-llm-finetuning-mlops](https://github.com/ajay1951/enterprise-llm-finetuning-mlops)
                """
            )

    # Wire up chat submit actions
    def user_submit(user_message, chat_history):
        if not user_message or not user_message.strip():
            return "", chat_history
        new_history = list(chat_history or []) + [[user_message, None]]
        return "", new_history

    def bot_stream(chat_history, sys_prompt, temp, max_tok, tp):
        if not chat_history:
            return chat_history, "Ready."
        user_msg = chat_history[-1][0]
        prior_history = chat_history[:-1]

        for bot_reply, telem in chat_response(
            message=user_msg,
            history=prior_history,
            system_prompt=sys_prompt,
            temperature=temp,
            max_tokens=max_tok,
            top_p=tp,
        ):
            chat_history[-1][1] = bot_reply
            yield chat_history, telem

    msg_input.submit(
        user_submit, [msg_input, chatbot], [msg_input, chatbot], queue=False
    ).then(
        bot_stream,
        [
            chatbot,
            system_prompt_input,
            temperature_slider,
            max_tokens_slider,
            top_p_slider,
        ],
        [chatbot, telemetry_box],
    )

    submit_btn.click(
        user_submit, [msg_input, chatbot], [msg_input, chatbot], queue=False
    ).then(
        bot_stream,
        [
            chatbot,
            system_prompt_input,
            temperature_slider,
            max_tokens_slider,
            top_p_slider,
        ],
        [chatbot, telemetry_box],
    )

    clear_btn.click(
        lambda: ([], "Conversation reset."), None, [chatbot, telemetry_box], queue=False
    )

if __name__ == "__main__":
    # Pre-warm model on startup
    engine.load_model()
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)
