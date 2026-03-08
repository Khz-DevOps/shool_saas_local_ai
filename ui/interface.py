import json
import datetime
import config
import gradio as gr
import requests
import agent.core as core

CSS = """
footer { display: none !important; }

.settings-box {
    background: var(--block-background-fill);
    border: 1px solid var(--block-border-color);
    border-radius: 10px;
    padding: 12px 16px;
}
"""

# ── Formatting helpers ─────────────────────────────────────────────────────────

def _fmt_tool_call(step_num: int, name: str, args: dict, elapsed: float) -> str:
    """Render a tool-call bubble (amber style via markdown)."""
    try:
        args_str = json.dumps(args, ensure_ascii=False, indent=2)
    except Exception:
        args_str = str(args)
    ts = datetime.datetime.now().strftime("%b %d, %Y, %I:%M:%S %p")
    return (
        f"---\n"
        f"**⚡ Tool Call** &nbsp;|&nbsp; `{name}`\n\n"
        f"```json\n{args_str}\n```\n"
        f"<sub>Step: {step_num} &nbsp;·&nbsp; {ts} &nbsp;·&nbsp; ⏱ {elapsed:.3f}s</sub>\n\n"
        f"---"
    )


def _fmt_tool_result(step_num: int, content: str, elapsed: float) -> str:
    """Render a tool-result bubble (teal style via markdown)."""
    # Pretty-print if valid JSON
    try:
        parsed   = json.loads(content)
        body     = json.dumps(parsed, ensure_ascii=False, indent=2)
    except Exception:
        body = content
    ts = datetime.datetime.now().strftime("%b %d, %Y, %I:%M:%S %p")
    return (
        f"---\n"
        f"**📦 Tool Result**\n\n"
        f"```json\n{body}\n```\n"
        f"<sub>Step: {step_num} &nbsp;·&nbsp; {ts} &nbsp;·&nbsp; ⏱ {elapsed:.3f}s</sub>\n\n"
        f"---"
    )


# ── Ollama helpers ─────────────────────────────────────────────────────────────

def _fetch_ollama_models() -> list[str]:
    try:
        resp = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5).json()
        return [m["name"] for m in resp.get("models", [])]
    except Exception:
        return [config.MODEL_NAME]


# ── Chat handler ───────────────────────────────────────────────────────────────

def _chat(user_message: str, chat_display: list, history: list, step_counter: int):
    if not user_message.strip():
        return "", chat_display, history, step_counter

    step_counter += 1

    try:
        reply, new_history, steps, elapsed = core.invoke(user_message, history)
    except Exception as e:
        reply       = f"⚠️ خطأ: {e}"
        new_history = history
        steps       = []
        elapsed     = 0.0

    ts = datetime.datetime.now().strftime("%b %d, %Y, %I:%M:%S %p")

    msgs: list[dict] = []

    # User message
    msgs.append({
        "role":    "user",
        "content": f"{user_message}\n\n<sub>Step: {step_counter} &nbsp;·&nbsp; {ts}</sub>",
    })

    # Tool call + result pairs
    call_num = 0
    for s in steps:
        if s["type"] == "tool_call":
            call_num += 1
            msgs.append({
                "role":    "assistant",
                "content": _fmt_tool_call(step_counter, s["name"], s["args"], elapsed),
            })
        elif s["type"] == "tool_result":
            msgs.append({
                "role":    "assistant",
                "content": _fmt_tool_result(step_counter, s["content"], elapsed),
            })

    # Final assistant response
    if reply:
        input_tokens  = sum(len(str(m)) for m in new_history) // 4   # rough estimate
        output_tokens = len(reply) // 4
        msgs.append({
            "role":    "assistant",
            "content": (
                f"{reply}\n\n"
                f"<sub>Step: {step_counter} &nbsp;·&nbsp; {ts} &nbsp;·&nbsp; "
                f"⏱ {elapsed:.3f}s &nbsp;·&nbsp; "
                f"~{input_tokens} in / ~{output_tokens} out tokens</sub>"
            ),
        })

    return "", chat_display + msgs, new_history, step_counter


def _clear():
    return [], [], 0


def _apply_settings(model: str, thinking: bool):
    return core.update_settings(model, thinking)


def _refresh_models():
    models = _fetch_ollama_models()
    return gr.Dropdown(choices=models, value=models[0] if models else config.MODEL_NAME)


# ── Build UI ───────────────────────────────────────────────────────────────────
with gr.Blocks(title="مساعد المدرسة", css=CSS, theme=gr.themes.Soft()) as demo:

    # ── Header ─────────────────────────────────────────
    gr.Markdown(
        "<div style='text-align:center'>"
        "<h1>🏫 مساعد المدرسة</h1>"
        "<p style='color:gray'>أهلاً وسهلاً! اسألني عن خدمات المدرسة أو أي استفسار تعليمي.</p>"
        "</div>"
    )

    # ── Settings row ───────────────────────────────────
    gr.Markdown("### ⚙️ الإعدادات")
    with gr.Row(elem_classes="settings-box"):
        model_dd = gr.Dropdown(
            choices            = _fetch_ollama_models(),
            value              = config.MODEL_NAME,
            allow_custom_value = True,
            label              = "النموذج",
            scale              = 4,
        )
        refresh_btn = gr.Button("🔄 تحديث", scale=1, min_width=90)
        thinking_cb = gr.Checkbox(
            value = config.REASONING,
            label = "تفعيل التفكير",
            scale = 1,
        )
        apply_btn = gr.Button("✅ تطبيق", variant="primary", scale=1, min_width=90)

    settings_status = gr.Textbox(
        value       = "",
        label       = "حالة الإعدادات",
        interactive = False,
        lines       = 1,
        max_lines   = 1,
    )

    gr.Markdown("---")

    # ── Chat area ───────────────────────────────────────
    gr.Markdown("### 💬 المحادثة")
    chatbot = gr.Chatbot(
        label      = "",
        height     = 520,
        layout     = "bubble",
        rtl        = True,
        buttons    = ["copy"],
        show_label = False,
        render_markdown = True,
    )

    # Hidden state: LangChain message history + conversation step counter
    history_state = gr.State([])
    step_state    = gr.State(0)

    # ── Input row ───────────────────────────────────────
    with gr.Row():
        msg_box = gr.Textbox(
            placeholder = "اكتب رسالتك هنا...",
            label       = "رسالتك",
            lines       = 2,
            max_lines   = 4,
            scale       = 5,
            rtl         = True,
        )
        with gr.Column(scale=1, min_width=110):
            send_btn  = gr.Button("📤 إرسال",         variant="primary",   size="lg")
            clear_btn = gr.Button("🗑️ محادثة جديدة",  variant="secondary", size="sm")

    # ── Quick-action buttons ────────────────────────────
    gr.Markdown("**اختصارات سريعة:**")
    with gr.Row():
        btn_menu     = gr.Button("📋 قائمة الخدمات",   variant="secondary", size="sm")
        btn_register = gr.Button("📝 التسجيل",          variant="secondary", size="sm")
        btn_fees     = gr.Button("💰 الرسوم الدراسية", variant="secondary", size="sm")
        btn_contact  = gr.Button("📞 تواصل معنا",       variant="secondary", size="sm")
        btn_schedule = gr.Button("📅 جدول الدراسة",    variant="secondary", size="sm")
        btn_grades   = gr.Button("📊 النتائج",          variant="secondary", size="sm")

    # ── Wire events ─────────────────────────────────────
    _inputs  = [msg_box, chatbot, history_state, step_state]
    _outputs = [msg_box, chatbot, history_state, step_state]

    refresh_btn.click(_refresh_models, None, model_dd)
    apply_btn.click(_apply_settings, [model_dd, thinking_cb], settings_status)

    msg_box.submit(_chat, _inputs, _outputs)
    send_btn.click(_chat,  _inputs, _outputs)
    clear_btn.click(_clear, None, [chatbot, history_state, step_state])

    btn_menu.click(
        lambda d, h, s: _chat("قائمة الخدمات", d, h, s),
        [chatbot, history_state, step_state], _outputs,
    )
    btn_register.click(
        lambda d, h, s: _chat("كيف أسجل في المدرسة؟", d, h, s),
        [chatbot, history_state, step_state], _outputs,
    )
    btn_fees.click(
        lambda d, h, s: _chat("كم رسوم الدراسة؟", d, h, s),
        [chatbot, history_state, step_state], _outputs,
    )
    btn_contact.click(
        lambda d, h, s: _chat("كيف أتواصل مع المدرسة؟", d, h, s),
        [chatbot, history_state, step_state], _outputs,
    )
    btn_schedule.click(
        lambda d, h, s: _chat("اعرض جدول الدراسة", d, h, s),
        [chatbot, history_state, step_state], _outputs,
    )
    btn_grades.click(
        lambda d, h, s: _chat("كيف أطلع على نتائج ابني؟", d, h, s),
        [chatbot, history_state, step_state], _outputs,
    )
