import os
import random
import tkinter as tk
from tkinter import ttk
import sys
import time
import threading
from chatbot import ChatBot
from task_2 import PredictDelay
from task_3 import ContingencyPlan


class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.old_stdout = sys.stdout
        sys.stdout = self

    def write(self, message):
        if message != '\n':
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.insert(tk.END, f"{message}\n")
            self.text_widget.config(state=tk.DISABLED)
            self.text_widget.see(tk.END)

    def flush(self):
        pass  # This method is required for compatibility


class GUI:
    def __init__(self, root):
        self.intent = None
        self.current_intent = None
        self.root = root
        self.chatbot = ChatBot()
        self.setup_ui()
        self.stdout_redirector = StdoutRedirector(self.chat_display)  # Redirect stdout to the chat display
        self.initial_greeting()
        self.predict = PredictDelay()
        self.contingency = ContingencyPlan()

    def setup_ui(self):
        self.root.title("RailBot")
        self.root.geometry("600x500")
        self.root.configure(bg="#f0f0f0")

        # Configure the root grid and design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Create chat display
        self.chat_display = tk.Text(self.root, height=20, width=50, state=tk.DISABLED, bg="#fff", fg="#333",
                                    wrap=tk.WORD,
                                    padx=10, pady=10, font=("Helvetica", 12))
        self.chat_display.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.chat_display.tag_configure("user_message", foreground="#007bff", justify="right")
        self.chat_display.tag_configure("bot_message", foreground="#333", justify="left")

        # Create scrollbar
        scrollbar = ttk.Scrollbar(self.root, command=self.chat_display.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_display.config(yscrollcommand=scrollbar.set)

        # Create entry
        self.entry = ttk.Entry(self.root, width=50, font=("Helvetica", 12))
        self.entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.entry.bind("<Return>", self.send_message)

        # Create send button
        send_button = ttk.Button(self.root, text="Send", command=self.send_message)
        send_button.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

    def initial_greeting(self):
        greeting_message = "Hi, how can I help you?"
        self.slow_print(f"Chatbot:\n{greeting_message}", "bot_message")

    def send_message(self, event=None):
        user_input = self.entry.get()
        if user_input.lower() in ["exit", "quit", "bye"]:
            self.root.destroy()
        else:
            # Display user's message
            self.display_message(f"You:\n{user_input}", "user_message")
            # Clear the entry field after displaying user input
            self.entry.delete(0, tk.END)

            # Process user's message with ChatBot
            threading.Thread(target=self.process_user_input, args=(user_input,)).start()

    def process_user_input(self, user_input):
        kb_t1 = self.chatbot.load_knowledge_base()
        kb_t2 = self.predict.load_prediction_knowledge_base()
        kb_t3 = self.contingency.load_contingency_knowledge_base()
        if self.current_intent == "predict_delay":
            response, intent = self.predict.main(user_input)
            if intent != "" or intent is not None:
                self.current_intent = intent

        elif self.current_intent == "contingency_plans":
            response, intent = self.contingency.main(user_input)
            if intent != "" or intent is not None:
                self.current_intent = intent

        elif self.current_intent == "ask_all_details":
            response, intent = self.chatbot.main(user_input)
            if intent != "" or intent is not None:
                self.current_intent = intent
        else:
            if self.current_intent == "ask_all_details":
                self.intent = self.chatbot.get_intent(user_input, kb_t1)
                response = random.choice(kb_t2[self.intent]["responses"])
                print(self.intent)
            if self.current_intent == "predict_delay":
                self.intent = self.chatbot.get_intent(user_input, kb_t2)
                response = random.choice(kb_t3[self.intent]["responses"])
                print(self.intent)
            if self.current_intent == "contingency_plans":
                self.intent = self.chatbot.get_intent(user_input, kb_t3)
                response = random.choice(kb_t3[self.intent]["responses"])
                print(self.intent)
            else:
                self.intent = self.chatbot.get_intent(user_input, kb_t1)
                print(self.intent)

            if self.intent == "predict_delay":
                kb = kb_t2
                self.current_intent = "predict_delay"
                response, intent = self.predict.main(user_input)
            elif self.intent == "contingency_plans":
                kb = kb_t3
                self.current_intent = "contingency_plans"
                response, intent = self.contingency.main(user_input)
            elif self.intent == "ask_all_details":
                kb = kb_t1
                self.current_intent = "ask_all_details"
                response, intent = self.chatbot.main(user_input)
            else:
                response = "I am sorry I do not understand what you are saying. My capabilities are limited."
                return response

        self.schedule_display_message(f"Chatbot:\n{response}", "bot_message")

    def display_message(self, message, tag):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{message}\n", tag)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def schedule_display_message(self, message, tag, delay=0.01):
        self.root.after(0, self.slow_print, message, tag, delay)

    def slow_print(self, message, tag, delay=0.01):
        def _slow_print(i=0):
            if i < len(message):
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.insert(tk.END, message[i], tag)
                self.chat_display.config(state=tk.DISABLED)
                self.chat_display.see(tk.END)
                self.root.after(int(delay * 1000), _slow_print, i + 1)
            else:
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.insert(tk.END, "\n", tag)  # Ensure to move to a new line after message
                self.chat_display.config(state=tk.DISABLED)
                self.chat_display.see(tk.END)

        _slow_print()


if __name__ == "__main__":
    recorded_data = os.getcwd() + "/recorded_data.csv"

    def reset_recorded_data():
        with open(recorded_data, 'w') as f:
            f.write("departure,destination,date,time\n")

    reset_recorded_data()
    root = tk.Tk()
    gui = GUI(root)
    root.mainloop()
