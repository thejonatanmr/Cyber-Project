import tkMessageBox
from Tkinter import *
import tkFileDialog
from tkFont import *
import Client as Cl


class GUIClass(Tk):

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title_font = Font(family='Helvetica', size=16, weight="bold")

        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (LoginPage, FilePage, EndPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.client = Cl.Client()
        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        # Show a frame for the given page name
        frame = self.frames[page_name]
        frame.tkraise()


class LoginPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        login_label = Label(self, text="Login", font=self.controller.title_font)
        # login_label.pack(side="top", fill="x", pady=10)
        login_label.grid(column=0, row=0)

        self.user_label = Label(self, text="Username", font=("Arial", 12))
        self.user_label.grid(column=0, row=1)
        # self.user_label.pack(side="right")

        self.pass_label = Label(self, text="Password", font=("Arial", 12))
        self.pass_label.grid(column=0, row=2)
        # self.pass_label.pack(side="right")

        self.user_text = Entry(self, width=20)
        self.user_text.grid(column=1, row=1)
        # self.user_text.pack(side="left")

        self.pass_text = Entry(self, width=20, show="*")
        self.pass_text.grid(column=1, row=2)
        # self.pass_text.pack(side="left")

        self.login_button = Button(self, text="Login", command=self.check_login)
        # self.login_button.pack(side="bottom")
        self.login_button.grid(column=0, row=6)

        self.signup_button = Button(self, text="Sign Up", command=self.check_new_user)
        # self.signup_button.pack(side="bottom")
        self.signup_button.grid(column=1, row=6)
        self.pack()

    def check_login(self):
        try:
            self.controller.client.run()

        except:
            tkMessageBox.showerror("Server error", "Could not connect to the server please try again")

        if self.controller.client.login(self.user_text.get(), self.pass_text.get()):
            tkMessageBox.showinfo("Login successfully", "You successfully logged in as {}".format(self.user_text.get()))
            self.controller.show_frame("FilePage")

        else:
            tkMessageBox.showerror("Login Unsuccessful", "Could not login, maybe the user and the password were wrong")

    def check_new_user(self):
        try:
            self.controller.client.run()

        except:
            tkMessageBox.showerror("Server error", "Could not connect to the server please try again")

        if self.controller.client.new_user(self.user_text.get(), self.pass_text.get()):
            if self.controller.client.login(self.user_text.get(), self.pass_text.get()):
                tkMessageBox.showinfo("Login successfully",
                                      "You successfully signed up and logged in")
                self.controller.show_frame("FilePage")

            else:
                tkMessageBox.showerror("Login unsuccessful",
                                       "Did signed up but could not login")

        else:
            tkMessageBox.showerror("Signup unsuccessful", "Could not sign up, maybe the user is taken")


class FilePage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        label = Label(self, text="Please choose a file", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)

        file_button = Button(self, text="Browse", command=self.open_file)
        file_button.pack()

        continue_button = Button(self, text="Browse", command=self.can_continue)
        continue_button.pack()

    def open_file(self):
        file = tkFileDialog.askopenfilename()

    def can_continue(self):
        self.controller.show_frame("EndPage")


class EndPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        label = Label(self, text="Choose an operation", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)

        encrypt_button = Button(self, text="Encrypt", command=self.encrypt)
        encrypt_button.pack()

        decrypt_button = Button(self, text="Decrypt", command=self.decrypt())
        decrypt_button.pack()

    def encrypt(self):
        pass

    def decrypt(self):
        pass


if __name__ == "__main__":
    app = GUIClass()
    app.mainloop()

# def openFile():
#     file = tkFileDialog.askopenfilename()
#
#
# submit_button = Button(login_window, text="Submit", command=submit)
# submit_button.grid(column=0, row=6)
#
# openfile_button = Button(login_window, text="Open File", command=openFile)
# openfile_button.grid(column=6, row=6)
#
# login_window.mainloop()
