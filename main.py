from selenium import webdriver
from selenium.webdriver.common.by import By
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float

import random
import tkinter as tk

VOCABULARY_3000 = "https://www.ef.com/wwen/english-resources/english-vocabulary/top-3000-words/"


# # TODO 1: Fetch the vocabulary list by web scrapping
# # Keep Chrome browser open after program finishes
# chrome_options = webdriver.ChromeOptions()
# chrome_options.add_experimental_option("detach", True)
#
# driver = webdriver.Chrome(options=chrome_options)
# driver.get(VOCABULARY_3000)
#
# vocabularies_fetch = driver.find_elements(By.XPATH, value='//*[@id="main-content"]/div/div/section/div/div/p')
#
# words_list = vocabularies_fetch[0].text.split("\n")
# print(f"The length of words_list is: {len(words_list)}")
#
#
# # TODO 2: Store the vocabularies into database
# Create a New Database
class Base(DeclarativeBase):
    pass


# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///vocabulary.db"
db = SQLAlchemy(model_class=Base)
# initialize the app with the extension
db.init_app(app)


class Vocabulary(db.Model):
    __tablename__ = "vocabulary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    word: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


# Add the vocabularies into db
# with app.app_context():
#     db.create_all()
#     for i in range(len(words_list)):
#         new_word = Vocabulary(id=i, word=words_list[i])
#         db.session.add(new_word)
#         db.session.commit()

# # Quit the browser
# driver.quit()

# ====================================================


CANVAS_W = 280
CANVAS_H = 50
CANVAS_LINES_SPACE = 50
TOTAL_SEC = 60
ONE_PAGE_WORDS = 30
PAGES = 10
TOTAL_WORD_AMOUNTS = ONE_PAGE_WORDS * PAGES


# The index of the testing word at the moment
word_now = 0
# resetting value which serves the show_testing_words function to check whether to generate a new pool of words
is_reset = True
# Set this variable to avoid keeping typing after time's up
is_timesup = False

# timer var will be set later in countdown function to make
timer = None
time_consuming = 0
# Set to accumulate the correct words and characters amounts
word_correct = 0
char_correct = 0

# Retrieve the test words from db
words_test = []
# The canvas objects
canvases = []
# The words shown in canvases
canvas_word = None

# This is to show the page, and check whether to show a new few canvases(words)
rnd = 0


def show_testing_words(reset: bool):
    '''If reset happens, it generates new testing words list from db, and the first few canvases to show the words.
    If the few canvases(words) have been answered, it will show the next few canvases(words).'''
    global canvases, words_test, canvas_word

    # If reset happens, it generates new testing words list from db.
    if reset:
        words_test = []
        canvases = []
        with app.app_context():
            for i in range(TOTAL_WORD_AMOUNTS):
                random_nums = random.randint(0, 3000)
                word = db.get_or_404(Vocabulary, random_nums)
                words_test.append(word)
                canvases.append(tk.Canvas(width=CANVAS_W, height=CANVAS_H, bg='white'))

    # Show few testing words in canvases.
    # If the few canvases(words) have been answered, it will show the next few canvases(words).
    for i in range(ONE_PAGE_WORDS):
        canvases[i + ONE_PAGE_WORDS * rnd].grid(column=i % 3, row=2 + i // 3, pady=5, padx=10)
        canvas_word = canvases[i + ONE_PAGE_WORDS * rnd].create_text((CANVAS_W / 2, CANVAS_H / 2),
                                                                     text=f"{words_test[i + ONE_PAGE_WORDS * rnd].word}",
                                                                     font=('Noto Sans Traditional Chinese', 32, 'bold'),
                                                                     fill='black')


def countdown(time_sec):
    '''Timer counts down'''
    global time_consuming, is_timesup
    # time_consuming var to calculate CPM and WPM in check_correctly function.
    time_consuming = TOTAL_SEC - time_sec
    timer_label.config(text=f"Time Left: {time_sec}")
    if time_sec > 0:
        # timer var for the after_cancel methods in reset function.
        global timer
        timer = window.after(1000, countdown, time_sec - 1)
    else:
        timer_label.config(text=f"Times Up", foreground='red')
        is_timesup = True


def reset():
    '''Reset game, including timer, vocabularies, WPM, CPM'''
    global is_reset, word_now, word_correct, char_correct, is_timesup, rnd

    # Exception catching to avoid resetting fail even when the timer hasn't started once.
    # Since timer argument is None by default, meaning it cannot be cancelled.
    try:
        window.after_cancel(timer)
    except:
        pass
    finally:
        # reset testing word index, correct words and chars amounts, rnd,
        word_now = 0
        word_correct = 0
        char_correct = 0
        rnd = 0

        # reset timer, page, WPM and CPM label
        timer_label.config(text=f"Resetting", foreground='white')
        WPM_label.config(text="WPM: ?")
        CPM_label.config(text="CPM: ?")
        page_label.config(text=f"Page {rnd + 1}")
        # Clear input_entry for reset
        input_entry.delete(0, tk.END)
        input_entry.after_idle(lambda: input_entry.configure(validate="key"))

        # reset is_timesup and is_rest to default
        is_timesup = False
        is_reset = True

        # Create a new pool of words and show them
        show_testing_words(is_reset)


def validate_entry(text, new_text):
    '''Define how to restrict the input type, and check whether the spelling is correct.'''
    global word_now, v, is_reset
    # If time's not up, user can type in. Otherwise, the input_entry is locked.
    if not is_timesup:
        checks = []
        # print(words_test[word_now].word)
        # Start count down if it's now reset, and start type in
        if is_reset:
            countdown(60)
            # Turn is_reset to False to ignore this if statement when countdown function is being executed.
            is_reset = False

        # Avoid typing in the chars over the length of (testing words + 1(one more space char))
        if len(text) > len(words_test[word_now].word) + 1:
            return False
        # Check the validation if the input is within the length of (testing words + 1(one more space char))
        else:
            # Using exception catching avoids checking the validation of the last space char
            try:
                # Check the chars match the words. If matched, append True to checks list; contractly, append False.
                for i, char in enumerate(text):
                    # If the chars typed in the input_entry corresponds to the words, make the canvas background green.
                    if char == words_test[word_now].word[i]:
                        checks.append(True)
                        canvases[word_now].config(background='green')
                    # If the chars typed in the input_entry don't corresponds to the words, make the canvas background red.
                    else:
                        checks.append(False)
                        canvases[word_now].config(background='red')
            # For checking the last char is space. Exception for the index error for an additional "space"
            except:
                if len(text) == len(words_test[word_now].word) + 1:
                    if new_text == " ":
                        global word_correct, char_correct, rnd
                        checks.append(True)
                        # Check the typed word just matched the entire words, clear the input_entry and make the answered canvas background gray and the texts blue
                        input_entry.delete(0, tk.END)
                        input_entry.after_idle(lambda: input_entry.configure(validate="key"))  # after_idle: https://stackoverflow.com/questions/52616268/python-tkinter-validation-command-not-working-after-deleting-entry
                        canvases[word_now].config(background='gray')
                        canvases[word_now].itemconfig(canvas_word, fill='blue')

                        word_correct += 1
                        char_correct += len(words_test[word_now].word)

                        # Update word_now for the next word index
                        word_now += 1
                        # Check whether words answered exceed the ONE_PAGE_WORDS.
                        # If yes, show new canvases(words) and updates page label
                        if word_now % ONE_PAGE_WORDS == 0:
                            rnd = int(word_now / ONE_PAGE_WORDS)
                            # print(f"rnd: {rnd}")
                            show_testing_words(is_reset)
                            page_label.config(text=f"Page {rnd+1}")

                        check_correctly()
                    # If the last char is not space, user cannot type in.
                    else:
                        checks.append(False)
        # Check all elements in checks list are True. If returned True, users could then type in.
        return all(checks)
    else:
        return False


def check_correctly():
    '''Calculate WPM and CPM and show them up'''
    # Exception catching to avoid finishing typing the first word with 1 sec, resulting to a zero division error
    try:
        wpm = round(word_correct / time_consuming * TOTAL_SEC, 1)
        cpm = round(char_correct / time_consuming * TOTAL_SEC, 1)
    except ZeroDivisionError:
        pass
    else:
        WPM_label.config(text=f"WPM: {wpm}")
        CPM_label.config(text=f"CPM: {cpm}")


window = tk.Tk()

window.title('Typing Speed Test')  # Add window title
window.minsize(width=960, height=900)  # Scale the window
window.geometry('+200+100')  # Let the window pop up at a certain position on the screen

reset_button = tk.Button(text="Restart", background='yellow', font=('helvetica', 16, 'bold'),
                         command=reset, activeforeground='blue')
reset_button.grid(column=2, row=0, pady=5)

timer_label = tk.Label(text="Resetting", font=('Noto Sans Traditional Chinese', 24, 'bold'))
timer_label.grid(column=2, row=1, pady=10, padx=10)

WPM_label = tk.Label(text="WPM: ?", font=('Noto Sans Traditional Chinese', 26, 'bold'))
WPM_label.grid(column=1, row=0, rowspan=2, pady=10, padx=10)

CPM_label = tk.Label(text="CPM: ?", font=('Noto Sans Traditional Chinese', 26, 'bold'))
CPM_label.grid(column=0, row=0, rowspan=2, pady=10, padx=10)

show_testing_words(is_reset)

page_label = tk.Label(text=f"Page {rnd+1}", font=('Noto Sans Traditional Chinese', 14, 'bold'))
page_label.grid(column=2, row=20, padx=10, sticky=tk.E)

v = tk.StringVar()
input_entry = tk.Entry(width=38, background='gray', textvariable=v, font=('New Times Roman', 36, 'bold'),
                       justify='center', validate="key", validatecommand=(window.register(validate_entry), "%P", "%S"))
input_entry.grid(column=0, row=21, columnspan=3, pady=10, padx=10)

type_here_label = tk.Label(text="↑\nType Here", font=('Noto Sans Traditional Chinese', 16, 'bold'))
type_here_label.grid(column=1, row=22, pady=5, padx=10)

window.mainloop()
