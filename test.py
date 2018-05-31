import tkMessageBox
from Tkinter import *
import tkFileDialog

login_window = Tk()
login_window.title("Login")
login_window.geometry('650x400')

login_label = Label(login_window, text="Login", font=("Arial", 16))
login_label.grid(column=0, row=0)

user_label = Label(login_window, text="Username", font=("Arial", 12))
user_label.grid(column=0, row=2)

pass_label = Label(login_window, text="Password", font=("Arial", 12))
pass_label.grid(column=0, row=4)

user_text = Entry(login_window, width=20)
user_text.grid(column=1, row=2)

pass_text = Entry(login_window, width=20)
pass_text.grid(column=1, row=4)


def submit():
    tkMessageBox.showinfo('Login', 'the user is {}, the password is {}'.format(user_text.get(), pass_text.get()))


def openFile():
    file = tkFileDialog.askopenfilename()


submit_button = Button(login_window, text="Submit", command=submit)
submit_button.grid(column=0, row=6)

openfile_button = Button(login_window, text="Open File", command=openFile)
openfile_button.grid(column=6, row=6)

login_window.mainloop()

# window = Tk()
# window.title("Encryption")
#
# lbl = Label(window, text="Hello", font=("Arial Bold", 32))
# lbl.grid(column=0, row=0)
#
# txt = Entry(window, width=10)
# txt.grid(column=1, row=0)
# txt.focus()
#
#
# def clicked():
#     res = txt.get()
#
#     lbl.configure(text=res)
#
#
# btn = Button(window, text="Click Me", bg="orange", fg="red", command=clicked)
# btn.grid(column=2, row=0)
#
# window.geometry('650x400')
#
# window.mainloop()
