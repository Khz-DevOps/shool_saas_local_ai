# شرح مشروع مساعد المطعم — سطر بسطر

---

## هيكل المشروع

```
AgentChatbot/
├── app.py              ← نقطة تشغيل البرنامج
├── config.py           ← كل الإعدادات في مكان واحد
├── requirements.txt    ← المكتبات المطلوبة
├── agent.log           ← ملف اللوج (يُنشأ تلقائياً عند التشغيل)
├── agent/
│   ├── __init__.py
│   ├── core.py         ← عقل الأجنت (التواصل مع Ollama)
│   └── tools.py        ← الأدوات الأربعة + قائمة الطعام
└── ui/
    ├── __init__.py
    └── interface.py    ← واجهة Gradio
```

---

## `config.py` — الإعدادات

```python
OLLAMA_BASE_URL = "http://localhost:11434"
```
عنوان سيرفر Ollama الشغّال على الجهاز.

```python
MODEL_NAME = "qwen3.5:0.8b"
```
اسم الموديل اللي هيستخدمه الأجنت. ممكن تغيّره من الواجهة.

```python
KEEP_ALIVE = -1
```
يخلي الموديل محمّل في الذاكرة للأبد (`-1`) عشان ميعملش reload كل طلب.
`0` = يمسحه من الذاكرة فور ما يخلّص. `"5m"` = يمسحه بعد 5 دقايق.

```python
TEMPERATURE = 0.7
```
درجة العشوائية في ردود الموديل. `0` = ردود ثابتة ودقيقة. `1` = أكثر إبداعاً وعشوائية.

```python
NUM_PREDICT = 512
```
أقصى عدد tokens (كلمات تقريباً) في كل رد.

```python
REASONING = False
```
تفعيل أو تعطيل وضع التفكير (Chain-of-Thought) في موديلات Qwen.
`True` = الموديل يفكر قبل ما يرد (أبطأ لكن أدق). `False` = يرد مباشرة.

```python
SERVER_PORT = 7860
```
البورت اللي هتفتح عليه الواجهة في المتصفح.

```python
OPEN_BROWSER = True
```
يفتح المتصفح تلقائياً عند تشغيل البرنامج.

```python
SHARE = True
```
ينشئ رابط عام على الإنترنت عبر Gradio Tunneling (مفيد للمشاركة مع غيرك).

---

## `app.py` — نقطة الدخول

```python
import config
from ui import demo
```
يستورد الإعدادات وكائن الواجهة الجاهزة من `ui/interface.py`.

```python
if __name__ == "__main__":
```
الكود اللي جوّاه بيشتغل بس لما تشغّل الملف مباشرة بـ `python app.py`.

```python
    print(f"🚀 Starting Agent Chatbot on http://localhost:{config.SERVER_PORT}")
```
يطبع رابط الواجهة في الـ Terminal.

```python
    demo.launch(
        server_port = config.SERVER_PORT,
        inbrowser   = config.OPEN_BROWSER,
        share       = config.SHARE,
        theme       = "soft",
        css         = "footer { display: none !important; }",
    )
```
يشغّل سيرفر Gradio بالإعدادات المحددة ويخفي الـ Footer.

---

## `requirements.txt` — المكتبات

```
gradio>=4.0.0
```
مكتبة بناء الواجهة التفاعلية في المتصفح.

```
langchain>=0.3.0
langchain-core>=0.3.0
langchain-community>=0.3.0
langchain-ollama>=0.2.0
```
مكتبة LangChain ومكوناتها — بنستخدمها فقط لتعريف الـ tools بالـ decorator `@tool`.

---

## `agent/tools.py` — الأدوات الأربعة

```python
import logging
from langchain_core.tools import tool
```
يستورد مكتبة اللوج و decorator الـ `@tool` من LangChain.

```python
log = logging.getLogger("agent")
```
يجيب الـ Logger المُعرَّف في `core.py` باسم `"agent"` عشان اللوج يظهر في نفس المكان.

```python
_order: list[dict] = []
```
قائمة في الذاكرة (RAM) بتحفظ طلب الزبون الحالي.
كل عنصر فيها شكله: `{"item": "برجر لحم", "price": 12.0, "qty": 2}`.

```python
MENU = { "starters": [...], "mains": [...], "drinks": [...], "desserts": [...] }
```
قاموس بيحتوي على قائمة الطعام مقسّمة لـ 4 أقسام.
كل صنف عنده اسم بالعربي وسعر.

```python
CAT_LABELS = { "starters": "🥗 المقبلات", ... }
```
قاموس لتحويل اسم القسم الإنجليزي إلى نص عربي مع إيموجي للعرض.

```python
def _find_item(name: str):
```
دالة داخلية (بتبدأ بـ `_` يعني مش للاستخدام الخارجي).
تبحث عن صنف بالاسم في قائمة الطعام وترجع الصنف أو `None` لو مش موجود.

---

### الأداة الأولى: `show_menu`

```python
@tool
def show_menu(category: str = "") -> str:
```
الـ `@tool` بيحوّل الدالة لأداة يقدر الأجنت يستخدمها.
بتاخد اسم القسم (اختياري) وترجع القائمة.

```python
    log.info("show_menu  category=%r  → showing %s", ...)
```
تسجّل في اللوج إن الأداة اتفعّلت وأي أقسام هتُعرض.

```python
    cats = [category] if category in MENU else list(MENU.keys())
```
لو الزبون طلب قسم معيّن يعرضه بس، غير كده يعرض كل الأقسام.

---

### الأداة الثانية: `add_to_order`

```python
@tool
def add_to_order(item_name: str, quantity: int = 1) -> str:
```
تضيف صنف للطلب. اسم الصنف إجباري، الكمية اختيارية (افتراضي 1).

```python
    item, _ = _find_item(item_name)
    if item is None:
        log.warning("add_to_order  NOT FOUND: %r", item_name)
        return f"❌ '{item_name}' غير موجود..."
```
لو الصنف مش موجود يسجّل تحذير في اللوج ويرجع رسالة خطأ للأجنت.

```python
    for entry in _order:
        if entry["item"] == item["name"]:
            entry["qty"] += qty
            return ...
```
لو الصنف موجود في الطلب بالفعل، يزيد كميته بدل ما يضيفه مرة ثانية.

```python
    _order.append({"item": item["name"], "price": item["price"], "qty": qty})
```
لو مش موجود، يضيفه كإدخال جديد في قائمة الطلب.

---

### الأداة الثالثة: `get_order_details`

```python
@tool
def get_order_details() -> str:
```
لا تاخد أي مدخلات. ترجع الطلب الحالي مع حساب الإجمالي.

```python
    total = 0.0
    for entry in _order:
        subtotal = entry["price"] * entry["qty"]
        total += subtotal
```
تحسب سعر كل صنف (السعر × الكمية) وتجمعهم للإجمالي الكلي.

---

### الأداة الرابعة: `confirm_order`

```python
@tool
def confirm_order() -> str:
```
تأكد الطلب وتطبع الفاتورة.

```python
    log.info("confirm_order  total=%.2f$  order cleared", total)
    _order.clear()
```
بعد ما تطبع الفاتورة، تفرّغ قائمة الطلب من الذاكرة.

```python
def reset_order():
    _order.clear()
```
دالة مساعدة تُستدعى لما الزبون يضغط "طلب جديد" في الواجهة.

---

## `agent/core.py` — عقل الأجنت

```python
import logging, requests, config
from agent.tools import show_menu, add_to_order, get_order_details, confirm_order, reset_order
```
يستورد المكتبات والأدوات.

### إعداد اللوج

```python
_fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
```
تنسيق رسائل اللوج: الوقت، مستوى الخطورة، الرسالة.

```python
_handler_console = logging.StreamHandler()
_handler_file    = logging.FileHandler("agent.log", encoding="utf-8")
```
ينشئ handler للكونسول وهاندلر تاني لحفظ اللوج في ملف `agent.log`.

```python
log = logging.getLogger("agent")
log.setLevel(logging.DEBUG)
log.addHandler(_handler_console)
log.addHandler(_handler_file)
```
ينشئ اللوجر باسم `"agent"` ويربطه بالاتنين (كونسول + ملف).
`DEBUG` = يسجّل كل المستويات (DEBUG, INFO, WARNING, ERROR).

### System Prompt

```python
_SYSTEM = ("أنت نادل مطعم ودود ومحترف.\n" ...)
```
التعليمات اللي بتحدد شخصية الأجنت وكيف يتصرف.
يتحدث العربية دايماً ويستخدم الأدوات لخدمة الزبون.

### تعريف الأدوات لـ Ollama

```python
_TOOLS = [{ "type": "function", "function": { "name": "show_menu", ... } }, ...]
```
قائمة بتوصف الأدوات بصيغة JSON Schema — هذا هو الـ format اللي Ollama بيفهمه.
كل أداة عندها: اسم، وصف، والـ parameters اللي بتاخدها.
هذه المعلومات بيبعتها للموديل عشان يعرف إيه الأدوات المتاحة وإزاي يستخدمها.

### ربط الأدوات بالكود

```python
_TOOL_FNS = {
    "show_menu":     lambda args: show_menu.invoke(args.get("category", "")),
    "add_to_order":  lambda args: add_to_order.invoke({...}),
    ...
}
```
قاموس بيربط اسم كل أداة بالدالة الفعلية في Python.
لما الموديل يقرر يستخدم أداة، هنبحث عن اسمها هنا وننفّذها.

```python
_URL    = f"{config.OLLAMA_BASE_URL}/api/chat"
_memory = [{"role": "system", "content": _SYSTEM}]
```
عنوان API الخاص بـ Ollama.
`_memory` = قائمة بتحتفظ بكل المحادثة (System + رسائل المستخدم + ردود الأجنت).

### دالة `invoke` — الحلقة الرئيسية

```python
def invoke(user_message: str) -> str:
    log.info("USER  → %s", user_message)
    _memory.append({"role": "user", "content": user_message})
```
تسجّل رسالة الزبون في اللوج وتضيفها لقائمة المحادثة.

```python
    while True:
        turn += 1
        log.debug("LLM call #%d  model=%s ...", turn, config.MODEL_NAME, ...)
```
حلقة لا نهائية — بتستمر لحد ما الأجنت يرد بنص (مش بأداة).
كل دورة = طلب HTTP واحد لـ Ollama.

```python
        resp = requests.post(_URL, json={
            "model":      config.MODEL_NAME,   # اسم الموديل
            "think":      config.REASONING,    # وضع التفكير
            "messages":   _memory,             # كل تاريخ المحادثة
            "tools":      _TOOLS,              # الأدوات المتاحة
            "stream":     False,               # نريد الرد دفعة واحدة
            "keep_alive": config.KEEP_ALIVE,   # يبقي الموديل في الذاكرة
            "options": { "temperature": ..., "num_predict": ... },
        }, timeout=120).json()
```
يبعت طلب HTTP POST لـ Ollama بكل البيانات ويستنى الرد.

```python
        msg = resp["message"]
        _memory.append(msg)
```
يحفظ رد الموديل في ذاكرة المحادثة.

```python
        if msg.get("tool_calls"):
            for call in msg["tool_calls"]:
                fn     = call["function"]["name"]
                args   = call["function"]["arguments"]
                log.info("TOOL CALL  → %s(%s)", fn, args)
                result = _TOOL_FNS[fn](args)
                log.info("TOOL RESULT← %s", ...)
                _memory.append({"role": "tool", "content": str(result)})
```
لو الموديل قرر يستخدم أداة:
  1. يستخرج اسم الأداة والمدخلات
  2. يسجّلها في اللوج
  3. ينفّذ الدالة الفعلية
  4. يسجّل النتيجة في اللوج
  5. يضيف النتيجة للمحادثة
  6. يعود للحلقة ويسأل الموديل مجدداً بالنتيجة

```python
        else:
            reply = msg.get("content", "")
            log.info("AGENT → %s", reply[:120] + ("…" if len(reply) > 120 else ""))
            return reply
```
لو الموديل رد بنص عادي (مش أداة)، يسجّله في اللوج ويرجعه للواجهة.

### دالة `reset`

```python
def reset():
    global _memory
    _memory = [{"role": "system", "content": _SYSTEM}]
    reset_order()
```
يمسح كل المحادثة ويبدأ من الأول (يحتفظ بالـ System prompt فقط).
`global _memory` = لأن `_memory` متغيّر خارج الدالة وعايزين نعيد تعريفه.

### دالة `update_settings`

```python
def update_settings(model: str, thinking: bool) -> str:
    config.MODEL_NAME = model.strip()
    config.REASONING  = thinking
```
يغيّر الموديل ووضع التفكير في الوقت الفعلي بدون إعادة تشغيل.
في Python، تغيير `config.MODEL_NAME` يأثر على كل الكود اللي بيقرأ منه.

---

## `ui/interface.py` — الواجهة

```python
import config, gradio as gr, requests
import agent.core as core
```
يستورد المكتبات والأجنت.

```python
def _fetch_ollama_models() -> list[str]:
    resp = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5).json()
    return [m["name"] for m in resp.get("models", [])]
```
يسأل Ollama عن الموديلات المثبّتة عبر `GET /api/tags` ويرجع أسماءها.
لو Ollama مش شغّال، يرجع الموديل الحالي من config.

```python
def _chat(user_message, history):
    reply = core.invoke(user_message)
    history.append({"role": "user",      "content": user_message})
    history.append({"role": "assistant", "content": reply})
    return "", history
```
بتبعت رسالة الزبون للأجنت وتضيف الرسالة والرد لقائمة المحادثة.
ترجع string فاضي (يمسح خانة الإدخال) وقائمة المحادثة المحدّثة.

```python
def _refresh_models():
    models = _fetch_ollama_models()
    return gr.Dropdown(choices=models, value=models[0] if models else config.MODEL_NAME)
```
تجيب قائمة الموديلات من Ollama وتحدّث الـ Dropdown في الواجهة.

```python
with gr.Blocks(title="مساعد المطعم", css=CSS, theme=gr.themes.Soft()) as demo:
```
ينشئ الواجهة بالـ theme الناعم وبعض تعديلات CSS.

```python
    model_dd = gr.Dropdown(choices=_fetch_ollama_models(), allow_custom_value=True, ...)
```
القائمة المنسدلة للموديلات — مبنية من Ollama مباشرة + تقدر تكتب أي اسم يدوياً.

```python
    refresh_btn.click(_refresh_models, None, model_dd)
```
زر 🔄 بيستدعي `_refresh_models` ويحدّث الـ Dropdown بالنتيجة.

```python
    apply_btn.click(_apply_settings, [model_dd, thinking_cb], settings_status)
```
زر تطبيق يبعت قيمة الـ Dropdown والـ Checkbox لـ `core.update_settings` ويعرض النتيجة.

```python
    btn_menu.click(lambda h: _chat("اعرض القائمة كاملة", h), [chatbot], [msg_box, chatbot])
```
أزرار الاختصارات السريعة — كل زر بيحاكي إن الزبون كتب رسالة معيّنة تلقائياً.

---

## سيناريو تشغيل كامل

```
1. المستخدم يشغّل: python app.py
2. Gradio يفتح على http://localhost:7860
3. المستخدم يكتب: "أريد برجر لحم واثنين عصير"
4. ui/interface.py → core.invoke("أريد برجر لحم واثنين عصير")
5. core.py → يبعت للـ Ollama: [system, user_message, tools]
6. Ollama يقرر يستخدم add_to_order("برجر لحم", 1)
7. core.py → ينفّذ الأداة → tools.py → يضيف للـ _order
8. core.py → يبعت نتيجة الأداة لـ Ollama
9. Ollama يقرر يستخدم add_to_order("عصير طازج", 2)
10. core.py → ينفّذ الأداة → tools.py → يضيف للـ _order
11. core.py → يبعت نتيجة الأداة لـ Ollama
12. Ollama يرد بنص: "تمّت الإضافة! هل تريد شيئاً آخر؟"
13. core.py → يرجع النص للـ ui
14. الواجهة تعرض الرد للمستخدم
15. كل خطوة مسجّلة في الكونسول وفي agent.log
```
