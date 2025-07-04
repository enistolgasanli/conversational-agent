import streamlit as st

from main import LangGraphBot
from langchain_core.messages import AIMessage, HumanMessage

class ChatApp:
    def __init__(self):
        self.initialize_session_state()
        self.bot = st.session_state.bot
        self.messages = st.session_state.messages

    def initialize_session_state(self):
        if "bot" not in st.session_state:
            st.session_state.bot = LangGraphBot()

        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you?"}]
 
    def display_messages(self):
        for msg in self.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    
    def convert_messages(self):
        converted = []

        for msg in self.messages:
            if msg["role"] == "user":
                converted.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                converted.append(AIMessage(content=msg["content"]))

        return converted
    
    def handle_user_input(self):
        user_input = st.chat_input("Write message")

        if user_input:
            self.messages.append({"role": "user", "content": user_input})

            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""

                for event in self.bot.app.stream(
                    {"messages": self.convert_messages()},
                    {"configurable": {"thread_id": "0"}}
                ):
                    for value in event.values():
                        if value["messages"] and isinstance(value["messages"][-1], AIMessage):
                            chunk = value["messages"][-1].content
                            
                            if chunk:
                                full_response += chunk
                                response_placeholder.markdown(full_response)

                response_placeholder.markdown(full_response)
                self.messages.append({"role": "assistant", "content": full_response})
        
    def run(self):
        self.display_messages()
        self.handle_user_input()

if __name__ == "__main__":
    app = ChatApp()
    app.run()