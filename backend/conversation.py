from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph


class Conversation:
    def __init__(self, chatbot, thread_id: str):
        self.chatbot = chatbot
        self.config = {"configurable": {"thread_id": thread_id}}
        self.prompt_template = self.setup_prompt()
        self.workflow = StateGraph(state_schema=MessagesState)
        self.memory = MemorySaver()
        self.app = None
        
    def start_chat(self):
        self.workflow.add_edge(START, "chatbot")
        self.workflow.add_node("chatbot", self.call_model)
        self.app = self.workflow.compile(checkpointer=self.memory)
        
    def chat_message(self, message: str):
        if self.app is None:
            raise ValueError("Chat not started")
        input_messages = [HumanMessage(message)]
        output = self.app.invoke({"messages": input_messages}, self.config)
        if "messages" in output and output["messages"]:
            output["messages"][-1].pretty_print()
        else:
            print("No response")
        
    def call_model(self, state: MessagesState):
        prompt = self.prompt_template.invoke(state)
        response = self.chatbot.invoke(prompt)
        return {"messages": response}
    
    def setup_prompt(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You're a personal assistant. Answer all questions to the best of your ability.",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return prompt_template
    