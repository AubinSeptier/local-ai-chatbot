from typing import List, Dict, AsyncIterator
from langchain_core.messages import HumanMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from ChatModel import CustomHuggingFaceChatModel

class Conversation:
    """
    Manages a conversation using LangGraph’s built-in persistence and asynchronous token streaming.
    Each conversation is identified by a thread_id (here the conversation_id),
    and the conversation history is automatically persisted.
    """
    def __init__(
        self,
        conversation_id: str,
        model: CustomHuggingFaceChatModel,
        max_history: int = 5,
        system_prompt: str = "You are a helpful assistant."
    ):
        self.id = conversation_id
        self.model = model  # your custom model must be instantiated with async streaming enabled
        self.max_history = max_history
        self.system_prompt = system_prompt

        # Build a simple state graph with a single agent node.
        self.workflow = StateGraph(state_schema=MessagesState)
        self.workflow.add_edge(START, "agent")
        self.workflow.add_node("agent", self.call_model)
        self.checkpointer = MemorySaver()
        self.graph = self.workflow.compile(checkpointer=self.checkpointer)

    async def call_model(self, state: MessagesState) -> Dict:
        """
        Asynchronously calls the model.
        Ensures a system message is added if needed, calls the model using the asynchronous streaming method,
        updates the conversation history, and returns the model’s response.
        When the graph is run with stream_mode="messages", the output will be token‐by‐token.
        """
        if not state["messages"] and self.system_prompt:
            state["messages"].append(HumanMessage(content=f"System: {self.system_prompt}"))
        # Call the model asynchronously (ensure your custom model implements ainvoke for async streaming)
        response = await self.model.ainvoke(state["messages"])
        state["messages"].append(response)
        # Trim history if too long.
        if len(state["messages"]) > self.max_history * 2:
            state["messages"] = state["messages"][-self.max_history * 2:]
        return {"messages": [response]}

    async def send_message(self, message: str) -> AsyncIterator[str]:
        """
        Sends a user message to the conversation and streams the assistant’s reply asynchronously.
        The graph is invoked with a configuration that uses the conversation_id as the thread identifier.
        By passing stream_mode="messages", only LLM token chunks are streamed.
        """
        input_state = {"messages": [HumanMessage(content=message)]}
        config = {"configurable": {"thread_id": self.id}}
        async for output in self.graph.astream(input_state, config=config, stream_mode="messages"):
            # Check if output is a tuple (e.g. (stream_mode, state)) and extract the state accordingly.
            if isinstance(output, tuple):
                state = output[1]
            else:
                state = output
            try:
                last_msg = state["messages"][-1]
            except (TypeError, IndexError):
                continue
            if hasattr(last_msg, "content") and last_msg.content.strip():
                yield last_msg.content

    def get_history(self) -> List[Dict]:
        """
        Returns the conversation history as a list of dicts.
        """
        config = {"configurable": {"thread_id": self.id}}
        state = self.graph.get_state(config).values
        return [{"role": msg.role, "content": msg.content} for msg in state["messages"]]

    def clear_history(self):
        """
        Clears the conversation history.
        """
        config = {"configurable": {"thread_id": self.id}}
        self.graph.update_state(config, {"messages": []})
