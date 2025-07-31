from langchain_core.tools import tool

@tool
def addition(a: int, b: int):
    """Add two numbers."""
    return a + b


def get_tools():
    return [addition]