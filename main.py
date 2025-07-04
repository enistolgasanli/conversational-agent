import os

from dotenv import load_dotenv
from langchain_community.tools import TavilySearchResults
from langchain.tools import Tool
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, ToolMessage

class LangGraphBot:
    def __init__(self):
        load_dotenv()
        self.huggingface_token = os.environ["HUGGINGFACE_API"]
        self.llm = self.load_llm()
        self.tools = self.load_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.tool_node = ToolNode(tools=self.tools)
        self.memory = MemorySaver()
        self.workflow = self.build_workflow()
        self.app = self.workflow.compile(checkpointer=self.memory)

    def load_llm(self):
        endpoint = HuggingFaceEndpoint(
            repo_id="Qwen/Qwen2.5-Coder-32B-Instruct",
            huggingfacehub_api_token=self.huggingface_token,
            task="text-generation",
            temperature=0.5
        )

        return ChatHuggingFace(llm=endpoint)
    
    def load_tools(self):
        tavily = TavilySearchResults(
            max_results=5,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True,
            include_images=True
        )

        return [tavily]
    
    def build_workflow(self):
        workflow = StateGraph(state_schema=MessagesState)

        workflow.add_node("chatbot", self.chatbot)
        workflow.add_node("tools", self.tool_node)

        workflow.add_edge(START, "chatbot")
        workflow.add_conditional_edges("chatbot", self.should_continue, ["tools", END])
        workflow.add_edge("tools", "chatbot")

        return workflow
    
    def should_continue(self, state: MessagesState):
        messages = state["messages"]

        if isinstance(messages[-1], AIMessage) and messages[-1].tool_calls:
            return "tools"
        
        if isinstance(messages[-1], ToolMessage):
            return "chatbot"
        
        return END

    def chatbot(self, state: MessagesState):
        messages = state["messages"]
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    def run(self):
        while True:
            try:
                user_input = input("User: ")

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("Goodbye")
                    break

                self.stream(user_input)
            except Exception as e:
                print(f"Exception occured: {e}")
                break

    def stream(self, user_input: str):
        for event in self.app.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            {"configurable": {"thread_id": "0"}}
        ):
            for value in event.values():
                if value["messages"][-1].content and isinstance(value["messages"][-1], AIMessage):
                    print("Assistant:", value["messages"][-1].content)

if __name__ == "__main__":
    bot = LangGraphBot()
    bot.run()