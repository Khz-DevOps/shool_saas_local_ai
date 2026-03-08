# =============================================
#  Project Configuration
# =============================================

# Ollama settings
OLLAMA_BASE_URL  = "http://localhost:11434"
MODEL_NAME       = "qwen3.5:0.8b"
KEEP_ALIVE       = -1        # -1 = keep model in memory forever, 0 = unload immediately, "5m" = 5 minutes
REQUEST_TIMEOUT  = 180       # seconds before giving up on a slow model response

# LLM settings
TEMPERATURE      = 0.7
NUM_PREDICT      = 2048      # max tokens to generate (512 was too small — caused "interrupted" errors)
NUM_CTX          = 8192      # context window size (system prompt alone is ~3000 tokens)
REASONING        = False     # True = enable Qwen thinking/CoT, False = disable

# ── Agent / School identity ────────────────────────────────────────────────
AGENT_NAME       = "مساعد المدرسة"
STORE_NAME       = "المدرسة"
WELCOME_MESSAGE  = (
    "أهلاً وسهلاً! 😊 أنا *مساعد المدرسة*، كيف يمكنني مساعدتك اليوم؟\n"
    "يمكنني مساعدتك في التسجيل، الرسوم، جداول الدراسة، والكثير من الخدمات. "
    "اضغط على *قائمة الخدمات* للاطلاع على كل ما يمكنني تقديمه."
)

# Gradio settings
SERVER_PORT     = 7860
OPEN_BROWSER    = True
SHARE           = True
