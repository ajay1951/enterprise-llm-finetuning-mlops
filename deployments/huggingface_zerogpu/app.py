"""ForgeLLM Public Hugging Face ZeroGPU Demo.

Interactive Gradio 5.x chat demonstration powered by ForgeLLM's inference engine
featuring a real-time live inference telemetry and observability panel.
"""

import os
import sys

# Ensure local imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import gradio as gr
except ImportError:
    gr = None

from adapter import ZeroGPUInferenceEngine

# Initialize inference engine instance and load model weights eagerly
engine = ZeroGPUInferenceEngine()
engine.load_model()

DEFAULT_SYSTEM_PROMPT = (
    "You are ForgeLLM, an enterprise-grade AI assistant specialized in LLMOps, "
    "fine-tuning pipelines, model evaluation, and production inference."
)

try:
    import spaces

    gpu_decorator = spaces.GPU(duration=60)
except (ImportError, AttributeError):

    def gpu_decorator(func):
        return func


@gpu_decorator
def chat_and_telemetry(
    message: str,
    history: list[dict[str, str]],
    system_prompt: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
):
    """Handle chat generation and yield streaming tokens with live telemetry updates."""
    if not message or not message.strip():
        yield history, "⚠️ Ready", "—", "—", "—", "—"
        return

    # Build ChatML formatted message array
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

    # Add user turn to chat history
    updated_history = list(history) + [
        {"role": "user", "content": message.strip()},
        {"role": "assistant", "content": ""},
    ]

    ttft_str = "—"
    latency_str = "—"
    tokens_str = "—"
    speed_str = "—"

    try:
        for chunk_text, telemetry in engine.generate_stream(
            messages=messages,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        ):
            updated_history[-1]["content"] = chunk_text

            if telemetry:
                ttft_val = telemetry.get("ttft_sec")
                lat_val = telemetry.get("latency_sec")
                tok_val = telemetry.get("tokens_generated")
                spd_val = telemetry.get("tokens_per_sec")

                ttft_str = f"{ttft_val:.2f} s" if ttft_val is not None else "—"
                latency_str = f"{lat_val:.2f} s" if lat_val is not None else "—"
                tokens_str = f"{tok_val}" if tok_val is not None else "—"
                speed_str = f"{spd_val:.1f} tok/s" if spd_val is not None else "—"

            yield (
                [dict(item) for item in updated_history],
                "⚡ Generating...",
                ttft_str,
                latency_str,
                tokens_str,
                speed_str,
            )

        yield (
            [dict(item) for item in updated_history],
            "✓ Complete",
            ttft_str,
            latency_str,
            tokens_str,
            speed_str,
        )
    except Exception as exc:
        yield (
            [dict(item) for item in updated_history],
            f"❌ Error: {exc}",
            "—",
            "—",
            "—",
            "—",
        )


def clear_chat():
    """Reset chat history and telemetry panel to initial state."""
    return [], "🟢 Ready", "—", "—", "—", "—"


def build_demo():
    """Construct Gradio Blocks interface with live inference telemetry panel."""
    if gr is None:
        return None

    custom_css = """
    .metrics-card {
        border-radius: 12px;
        padding: 16px;
        background: rgba(240, 244, 255, 0.6);
        border: 1px solid rgba(200, 215, 250, 0.8);
    }
    """

    with gr.Blocks(
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="indigo"),
        title="⚒️ ForgeLLM — Enterprise LLM Platform Demo",
        css=custom_css,
    ) as blocks_demo:
        gr.Markdown(
            """
            # ⚒️ ForgeLLM — Enterprise LLM Platform Demo
            **Live Inference Observability & Telemetry Demo** powered by `Qwen/Qwen2.5-0.5B-Instruct` on **Hugging Face ZeroGPU**.
            """
        )

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    type="messages",
                    height=480,
                    show_copy_button=True,
                )
                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Ask a technical question about LLMOps, LoRA fine-tuning, evaluation, or vLLM...",
                        show_label=False,
                        lines=1,
                        max_lines=4,
                        scale=4,
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)
                    clear_btn = gr.Button("Clear", variant="secondary", scale=1)

                with gr.Accordion(
                    label="⚙️ Generation Parameters & System Prompt", open=False
                ):
                    system_prompt_input = gr.Textbox(
                        label="System Prompt",
                        value=DEFAULT_SYSTEM_PROMPT,
                        lines=2,
                    )
                    with gr.Row():
                        temp_slider = gr.Slider(
                            label="Temperature",
                            minimum=0.0,
                            maximum=1.5,
                            value=0.7,
                            step=0.05,
                            info="Sampling randomness",
                        )
                        tokens_slider = gr.Slider(
                            label="Max New Tokens",
                            minimum=32,
                            maximum=512,
                            value=256,
                            step=32,
                            info="Max generation length",
                        )
                        topp_slider = gr.Slider(
                            label="Top-p",
                            minimum=0.1,
                            maximum=1.0,
                            value=0.8,
                            step=0.05,
                            info="Nucleus sampling threshold",
                        )

                gr.Examples(
                    examples=[
                        ["Explain how LoRA fine-tuning works in ForgeLLM."],
                        ["What is an OOM guardrail in GPU cluster orchestration?"],
                        ["Compare Hugging Face Transformers vs vLLM serving latency."],
                    ],
                    inputs=[msg_input],
                )

            with (
                gr.Column(scale=1),
                gr.Group(elem_classes=["metrics-card"]),
            ):
                gr.Markdown("### 📊 Live Inference Telemetry")
                status_box = gr.Textbox(
                    label="Status",
                    value="🟢 Ready",
                    interactive=False,
                )
                with gr.Row():
                    ttft_box = gr.Textbox(
                        label="TTFT",
                        value="—",
                        interactive=False,
                    )
                    latency_box = gr.Textbox(
                        label="Total Latency",
                        value="—",
                        interactive=False,
                    )
                with gr.Row():
                    tokens_box = gr.Textbox(
                        label="Output Tokens",
                        value="—",
                        interactive=False,
                    )
                    throughput_box = gr.Textbox(
                        label="Throughput",
                        value="—",
                        interactive=False,
                    )

                gr.Markdown("---")
                gr.Markdown("### ⚙️ Runtime Specifications")
                model_box = gr.Textbox(
                    label="Model",
                    value="Qwen2.5-0.5B-Instruct",
                    interactive=False,
                )
                backend_box = gr.Textbox(
                    label="Runtime Backend",
                    value="Transformers / ZeroGPU"
                    if "cuda" in engine.device
                    else "Transformers / CPU Fallback",
                    interactive=False,
                )
                precision_box = gr.Textbox(
                    label="Precision",
                    value="bfloat16" if "cuda" in engine.device else "float32",
                    interactive=False,
                )

        # Wire event handlers
        submit_btn.click(
            fn=chat_and_telemetry,
            inputs=[
                msg_input,
                chatbot,
                system_prompt_input,
                temp_slider,
                tokens_slider,
                topp_slider,
            ],
            outputs=[
                chatbot,
                status_box,
                ttft_box,
                latency_box,
                tokens_box,
                throughput_box,
            ],
            api_name=False,
            show_api=False,
        ).then(fn=lambda: "", outputs=[msg_input], api_name=False, show_api=False)

        msg_input.submit(
            fn=chat_and_telemetry,
            inputs=[
                msg_input,
                chatbot,
                system_prompt_input,
                temp_slider,
                tokens_slider,
                topp_slider,
            ],
            outputs=[
                chatbot,
                status_box,
                ttft_box,
                latency_box,
                tokens_box,
                throughput_box,
            ],
            api_name=False,
            show_api=False,
        ).then(fn=lambda: "", outputs=[msg_input], api_name=False, show_api=False)

        clear_btn.click(
            fn=clear_chat,
            outputs=[
                chatbot,
                status_box,
                ttft_box,
                latency_box,
                tokens_box,
                throughput_box,
            ],
            api_name=False,
            show_api=False,
        )

    return blocks_demo


demo = build_demo() if gr is not None else None

if __name__ == "__main__":
    if demo is not None:
        demo.launch()
