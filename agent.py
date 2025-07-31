from typing_extensions import TypedDict
from typing import Annotated, Optional
import uuid

from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.graph.state import StateGraph, START, END
from langchain_openai import ChatOpenAI

from langchain_core.messages import ToolMessage, SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver

from tools import get_tools # TODO: Add your own tools here! See tools.py
from prompts import get_agent_prompt # TODO: Add your own prompts here! See prompts.py

from dotenv import load_dotenv

load_dotenv(dotenv_path="./.env", override=True)

llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages] # Conversation history
    slack_user: str 
    query_plan: Optional[str] # TODO: Use in plan node!
    # TODO: Customize and add more fields as needed!

checkpointer = MemorySaver()
# Allows us to persist the state of the graph between invocations
# Essentially, enables conversation history to be maintained



tools = get_tools() # TODO: Add your own tools! See tools.py
llm_with_tools = llm.bind_tools(tools)

# ------------------------------------------------------------------------------------------------
# Nodes --------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------


# Define a node that actually executes the tools that your LLM model calls.
# This is a prebuilt node that LangGraph provides.
tool_node = ToolNode(tools)


# Main LLM Agent Node
def agent_node(state: State, config: RunnableConfig): 
    prompt = get_agent_prompt(user=state["slack_user"])
    
    # TODO: filter the messages in the state if you're interested!
    # The state messages contains a continuously appending list of messages
    # in the conversation history.
    conversation_history = [SystemMessage(prompt)] + state["messages"]
    
    # NOTE: LangGraph supports custom primitives to reset or remove messages (see add_messages reducer)
    
    # Invoke the model
    response = llm_with_tools.invoke(conversation_history) 

    # Update the state, adding this message to the conversation history.
    # By default, returned state replaces the existing state - messages 
    # has been configured with add_messages to append to the existing list.
    return {"messages": [response]}

# TODO: You can add a node that creates a plan for the agent to follow.
def plan_node(state: State, config: RunnableConfig):
    pass

# Conditional edge that determines whether to continue execution or not
def should_continue(state: State, config: RunnableConfig):
    messages = state["messages"]
    last_message = messages[-1]
    
    # NOTE: We're assuming that if the agent is done calling tools,
    # then it has completed its task and wants to respond to the user

    # If there is no tool call from the AI, we pass the response to the user.
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue letting the agent call tools.
    else:
        return "continue"
    

# ------------------------------------------------------------------------------------------------
# Linking the Graph Together ---------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------

def make_graph(checkpointer):
    graph = StateGraph(State)

    # Add nodes 
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    # TODO: Add your plan node here!

    # Add edges 
    # First, we define the start node. The query will always route to the agent node first. 
    graph.add_edge(START, "agent")
    # TODO: You could always make a plan first, and always route to the agent node.

    # We now add a conditional edge
    graph.add_conditional_edges(
        "agent",
        # Function representing our conditional edge
        should_continue,
        {
            # If `tools`, then we call the tool node.
            "continue": "tools",
            # Otherwise we finish.
            "end": END,
        },
    )

    # After executing a tool call, always send the result to the agent.
    graph.add_edge("tools", "agent")
    graph = graph.compile(name="assistant", checkpointer=checkpointer)
    return graph


# ------------------------------------------------------------------------------------------------
# Run the Graph Agent ---------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------

def run_graph(checkpointer):
    graph = make_graph(checkpointer)

    config = {"configurable": {"thread_id": uuid.uuid4()}} 
    # The config lets us set additional metadata, including a thread_id
    # which is equivalent to an ID for a conversation.

    input = {
        "messages": [HumanMessage(content="What is 1 + 1?")],
        "slack_user": "Robert Xu"
    }
    result = graph.invoke(input, config=config) # TODO: You can also stream
    # By default this returns the final state of the graph

    for message in result["messages"]:
        if message.content:
            print(message.type + ": " + message.content)

    print("Next Human Message --------------------------------")
    
    new_input = {
        "messages": [HumanMessage(content="Now what is 1 + 2?")],
        "slack_user": "Robert Xu"
    }
    result = graph.invoke(new_input, config=config)
    # NOTE: The previous messages are still in the conversation history!
    # Sending new requests will append to the existing conversation history
    # because we used a checkpointer
    
    for message in result["messages"]:
        if message.content:
            print(message.type + ": " + message.content)

if __name__ == "__main__":
    run_graph(checkpointer)