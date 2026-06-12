"""
Mock LLM used by the deployment lab.
No real API key is required, so the app can run offline.
"""
import random
import time


MOCK_RESPONSES = {
    "default": [
        "This is a mock AI agent response. In production, this can be replaced with OpenAI or another LLM provider.",
        "The agent is running correctly. Your request was received and processed.",
        "I am a cloud-ready AI agent. The deployment pipeline is working.",
    ],
    "docker": ["Containers package an app so it can run consistently across environments."],
    "deploy": ["Deployment is the process of moving code from a local machine to a public runtime environment."],
    "health": ["The agent is healthy and ready to serve traffic."],
}


def ask(question: str, delay: float = 0.1) -> str:
    time.sleep(delay + random.uniform(0, 0.05))

    question_lower = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in question_lower:
            return random.choice(responses)

    return random.choice(MOCK_RESPONSES["default"])


def ask_stream(question: str):
    response = ask(question)
    for word in response.split():
        time.sleep(0.05)
        yield word + " "
