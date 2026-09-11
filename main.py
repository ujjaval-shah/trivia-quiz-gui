import tkinter as tk
from tkinter import ttk
import requests
import random
import html
import time
from threading import Thread


class QuizGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trivia Quiz")
        self.geometry("1100x700")
        self.resizable(False, False)

        self.style = ttk.Style(self)
        self.style.configure("TButton", font=("Helvetica", 15))
        self.style.configure("TRadiobutton", font=("Helvetica", 15))

        self.grid_columnconfigure(0, weight=1)

        self.title_label = ttk.Label(self, text="Trivia Quiz", font=("Helvetica", 25, "bold"))
        self.title_label.grid(row=0, column=0, sticky="ew", padx=15, pady=(25, 10))

        separator = ttk.Separator(self, orient="horizontal")
        separator.grid(row=1, column=0, sticky="ew", padx=15, pady=5)

        self.container = ttk.Frame(self)
        self.container.grid(row=2, column=0, sticky="nsew")

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.home_page = HomePage(self.container, self)
        self.home_page.grid(row=0, column=0, sticky="nsew")

    def unescape_data(self, data):
        if isinstance(data, str):
            return html.unescape(data)
        elif isinstance(data, list):
            return [self.unescape_data(item) for item in data]
        elif isinstance(data, dict):
            return {key: self.unescape_data(value) for key, value in data.items()}
        return data

    def api_call(self):
        api_url = "https://opentdb.com/api.php?amount=10&difficulty=easy&type=multiple"
        delay = 1

        while True:
            try:
                response = requests.get(api_url, timeout=5)
                response.raise_for_status()
                print(f"Request succeeded! Status Code: {response.status_code}")
                return response.json()

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)

    def fetch_data(self):
        data = self.api_call()
        processed_data = self.unescape_data(data["results"])

        questions = []
        for q in processed_data:
            options = q["incorrect_answers"] + [q["correct_answer"]]
            random.shuffle(options)
            questions.append({
                "question": q["question"],
                "correct_answer": q["correct_answer"],
                "options": options
            })

        return questions

    def show_frame(self, q_no):
        self.q_state = q_no
        self.question_frames[self.q_state - 1].tkraise()

    def on_start(self):
        self.questions = self.fetch_data()
        self.selected_options = [tk.IntVar(value=-1) for i in range(len(self.questions))]
        self.question_frames = [QuestionPage(self.container, self, i+1, q_data, self.selected_options[i]) for i, q_data in enumerate(self.questions)]
        for q_frame in self.question_frames:
            q_frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(q_no=1)

    def on_next(self):
        self.show_frame(min(10, self.q_state + 1))

    def on_prev(self):
        self.show_frame(max(1, self.q_state - 1))

    def generate_result(self):
        score = 0
        result = []
        for i in range(len(self.questions)):
            correct_choice = self.questions[i]["options"].index(self.questions[i]["correct_answer"])
            user_choice = self.selected_options[i].get()
            score += correct_choice == user_choice
            chosen_option = "" if user_choice == -1 else self.questions[i]["options"][user_choice]
            result.append(
                f'{i+1}. {self.questions[i]["question"]}\nCorrect Answer: {self.questions[i]["correct_answer"]}\nYour Response: {chosen_option}'
            )
        return score, "\n\n".join(result)

    def on_submit(self):
        score, result_text = self.generate_result()
        print(f">> Score: {score}/10")
        result_page = ResultPage(self.container, self, score, len(self.questions), result_text)
        result_page.grid(row=0, column=0, sticky="nsew")
        result_page.tkraise()


class HomePage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        sentences = [
            "Quiz GUI App made with Tkinter. Press start button to start the quiz.",
            "Make sure you have active internet connection.",
            "The questions will take a few seconds to load."
        ]

        label = ttk.Label(
            self, text="\n".join(sentences),
            font=("Helvetica", 15)
        )
        label.grid(row=1, column=0, sticky="w", padx=15, pady=15)

        self.start_btn = ttk.Button(
            self,
            text="Start",
            command=self.on_start
        )
        self.start_btn.grid(row=2, column=0, sticky="w", padx=15, pady=15)
    
    def on_start(self):
        print(">> Start Button Clicked")
        self.start_btn.config(state=tk.DISABLED)
        Thread(target=self.controller.on_start).start()


class QuestionPage(ttk.Frame):
    def __init__(self, parent, controller, question_no, question_data, selected_option):
        super().__init__(parent)
        self.controller = controller
        self.question_no = question_no
        self.selected_option = selected_option

        self.grid_columnconfigure(1, weight=1)

        question_no_label = ttk.Label(
            self,
            text=f"Question Number: {self.question_no}",
            font=("Helvetica", 20, "bold")
        )
        question_no_label.grid(
            row=0, column=0,
            columnspan=3,
            sticky="w",
            padx=15, pady=(15, 10)
        )

        question_text_label = ttk.Label(
            self,
            text=question_data["question"],
            wraplength=1050,
            justify="left",
            font=("Helvetica", 15)
        )
        question_text_label.grid(
            row=1, column=0,
            columnspan=3,
            sticky="w",
            padx=15, pady=10
        )

        options_frame = ttk.Frame(self)
        options_frame.grid_columnconfigure(0, weight=1)

        options_frame.grid(
            row=2, column=0,
            columnspan=3,
            sticky="w",
            padx=15, pady=10
        )

        for i, option in enumerate(question_data["options"]):
            rbtn = ttk.Radiobutton(
                options_frame,
                text=option,
                variable=selected_option,
                value=i,
                command=self.test_radiobtn
            )
            rbtn.grid(row=i, column=0, sticky="w")

        prev_btn = ttk.Button(
            self, text="Previous",
            command=controller.on_prev
        )
        prev_btn.grid(
            row=3, column=0,
            sticky="w",
            padx=15, pady=15
        )

        next_btn = ttk.Button(
            self, text="Next",
            command=controller.on_next
        )
        next_btn.grid(
            row=3, column=1,
            sticky="w",
            padx=15, pady=15
        )

        submit_btn = ttk.Button(
            self, text="Submit",
            command=controller.on_submit
        )
        submit_btn.grid(
            row=3, column=2,
            sticky="e",
            padx=15, pady=15
        )

    def test_radiobtn(self):
        print(f">> Question Number {self.question_no} Option {self.selected_option.get() + 1} selected")


class ResultPage(ttk.Frame):
    def __init__(self, parent, controller, score, total, generated_result):
        super().__init__(parent)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.score_label = ttk.Label(
            self,
            text=f"Quiz Completed! Your Score: {score}/{total}",
            font=("Helvetica", 20, "bold")
        )
        self.score_label.grid(
            row=0, column=0,
            sticky="w",
            padx=15, pady=(15, 10)
        )

        result_text_area = tk.Text(self, wrap=tk.WORD, font=("Helvetica", 14))
        result_text_area.insert(tk.END, generated_result)
        result_text_area.config(state=tk.DISABLED)
        result_text_area.grid(
            row=1, column=0,
            sticky="nsew",
            padx=15, pady=15
        )


if __name__ == "__main__":
    quiz_gui = QuizGUI()
    quiz_gui.mainloop()