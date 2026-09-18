import ollama

MODEL = "llama3.2"

SYSTEM_PROMPT = (
    "Must reply like this is an iMessage conversation. *Maximum length of reply 1 sentance*. "
    "Act as this personality and adapt typing habits. "
    "(if random, then choose a random personality in the initial response "
    "and then use it for entire conversation) PERSONALITY: {name}"
)


def build_messages(personality, history):
    cleaned = [{"role": m["role"], "content": m["content"]} for m in history]
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(name=personality)}]
    messages.extend(cleaned)
    return messages


def chat(personality, history):
    response = ollama.chat(
        model=MODEL,
        messages=build_messages(personality, history),
    )
    return response["message"]["content"]