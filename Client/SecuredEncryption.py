import tkMessageBox
from Tkinter import *
from ttk import *
import tkFileDialog
from tkFont import *
import Code.ClientSide as Cl
import ConfigParser



class GUIClass(Tk):

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title_font = Font(family='Helvetica', size=16, weight="bold")

        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.config = ConfigParser.RawConfigParser()
        self.config.read("SecuredEncryption.ini")

        self.frames = {}
        self.raised_frame = None

        for F in (LoginPage, FilePage, EncDecPage, WorkingPage, FinishPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.file = ""
        self.client_side = Cl.ClientSide(self)
        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        # Show a frame for the given page name
        self.raised_frame = self.frames[page_name]
        self.raised_frame.tkraise()

    def raise_error_box(self, error_header, error_message, move_frame=False, frame=""):
        tkMessageBox.showerror(error_header, error_message)
        if move_frame:
            self.show_frame(frame)


class LoginPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.connected = False
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

    def check_connected(self):
        if self.connected:
            return True
        else:
            self.connected = self.controller.client_side.run()
            return self.connected

    def check_login(self):
        if self.check_connected():

            if self.controller.client_side.login(self.user_text.get(), self.pass_text.get()):
                tkMessageBox.showinfo("Login successfully", "You successfully logged in as {}".format(self.user_text.get()))
                self.controller.show_frame("FilePage")

    def check_new_user(self):
        if self.check_connected():

            if self.controller.client_side.new_user(self.user_text.get(), self.pass_text.get()):
                if self.controller.client_side.login(self.user_text.get(), self.pass_text.get()):
                    tkMessageBox.showinfo("Login successfully",
                                          "You successfully signed up and logged in")
                    self.controller.show_frame("FilePage")


class FilePage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.last_opened = self.controller.config.get("UI", "file_path")

        label = Label(self, text="Please choose a file", font=controller.title_font)
        label.grid(column=0, row=0)

        file_button = Button(self, text="Browse", command=self.open_file)
        file_button.grid(column=1, row=1)

        self.file_path_text = Entry(self, width=80, )
        self.file_path_text.grid(column=0, row=1)
        self.file_path_text.delete(0, END)
        self.file_path_text.insert(0, self.last_opened)

        continue_button = Button(self, text="Next", command=self.can_continue)
        continue_button.grid(column=0, row=2)
        self.pack()

    def open_file(self):
        file_path = tkFileDialog.askopenfilename(initialdir=self.last_opened)
        self.file_path_text.delete(0, END)
        self.file_path_text.insert(0, file_path)
        self.last_opened = "".join(file_path.split("/")[0:-1])

    def can_continue(self):
        with open("SecuredEncryption.ini", 'wb') as config_file:
            self.controller.config.write(config_file)

        self.controller.file = self.file_path_text.get()
        if self.controller.client_side.check_enc_file(self.controller.file):
            tkMessageBox.showinfo("Encrypted file detected", "The file chosen is detected as an encrypted file. "
                                                             "moving to decryption")
            self.controller.frames["EncDecPage"].operation.set("decrypt")
            self.controller.frames["EncDecPage"].continue_next_page()
        else:
            self.controller.show_frame("EncDecPage")


class EncDecPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller

        self.operation = StringVar()
        self.type = StringVar()

        label = Label(self, text="Choose an operation", font=controller.title_font)
        label.grid(column=0, row=0)

        self.encryption_radio = Radiobutton(self, text="Encrypt", variable=self.operation, value="encrypt", command=self.update_radio_encrypt)
        self.encryption_radio.grid(column=0, row=1)

        self.decrypt_radio = Radiobutton(self, text="Decrypt", variable=self.operation, value="decrypt", command=self.update_radio_decrypt)
        self.decrypt_radio.grid(column=1, row=1)

        label = Label(self, text="Choose a type of encryption", font=controller.title_font)
        label.grid(column=0, row=2)

        self.AES_radio = Radiobutton(self, text="AES", variable=self.type, value="aes", state="disabled")
        self.AES_radio.grid(column=0, row=3)

        self.Builtin_radio = Radiobutton(self, text="BlowFish", variable=self.type, value="blowfish", state="disabled")
        self.Builtin_radio.grid(column=0, row=4)

        self.continue_button = Button(self, text="continue", command=self.continue_next_page)
        self.continue_button.grid(column=1, row=5)

        self.return_button = Button(self, text="Return", command=self.return_page)
        self.return_button.grid(column=0, row=5)

    def return_page(self):
        self.controller.show_frame("FilePage")

    def update_radio_encrypt(self):
        self.Builtin_radio['state'] = "normal"
        self.AES_radio['state'] = "normal"

    def update_radio_decrypt(self):
        self.Builtin_radio['state'] = "disabled"
        self.AES_radio['state'] = "disabled"

    def continue_next_page(self):
        self.controller.show_frame("WorkingPage")
        if self.operation.get() == "encrypt":
            self.controller.client_side.encrypt(self.controller.file, self.type.get())
        else:
            self.controller.client_side.decrypt(self.controller.file)


class WorkingPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        label = Label(self, text="Working", font=controller.title_font)
        label.grid(column=0, row=0)

        self.progress = Progressbar(self, orient="horizontal", length=120, mode="determinate")
        self.progress.grid(column=0, row=1)
        self.progress["value"] = 0
        self.progress["maximum"] = 100

        self.pack()

    def update_progress(self, current, max_value):
        prec = (current / max_value) * 100
        self.progress["value"] = prec

    def next_page(self):
        self.controller.show_frame("FinishPage")


class FinishPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        label = Label(self, text="Finished", font=controller.title_font)
        label.grid(column=0, row=0)

        finish_button = Button(self, text="Finish", command=self.start_again)
        finish_button.grid(column=0, row=1)

        exit_button = Button(self, text="Exit", command=self.exit_ui)
        exit_button.grid(column=1, row=1)

    def start_again(self):
        self.controller.show_frame("FilePage")

    def exit_ui(self):
        self.controller.client_side.exit()
        self.controller.destroy()


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
