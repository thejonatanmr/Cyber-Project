import sys
import os

sys.path.append(os.getcwd() + "\\code\\libs")

import tkMessageBox
from Tkinter import *
from ttk import *
import tkFileDialog
from tkFont import *
import Code.ClientSide as Cl
import ConfigParser
import os


class GUIClass(Tk):
    """The main GUI class"""

    def __init__(self, *args, **kwargs):
        """Sets the initial variables values."""
        Tk.__init__(self, *args, **kwargs)

        self.title_font = Font(family='Helvetica', size=14, weight="bold")
        self.file = ""

        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.config = ConfigParser.RawConfigParser()
        self.config.read("SecuredEncryption.ini")

        self.frames = {}
        self.raised_frame = None

        for F in (LoginPage, FilePage, EncDecPage, FinishPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.client_side = Cl.ClientSide(self)
        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        """Show a frame for the given page name"""
        self.raised_frame = self.frames[page_name]
        self.raised_frame.tkraise()

    def raise_error_box(self, error_header, error_message, move_frame=False, frame=""):
        """Raising an error box. if given a frame moving to that frame.

        :param error_header: the header of the error box
        :param error_message: the message of the error box
        :param move_frame: True - moves a frame, False - not moving a frame
        :param frame: the frame to move
        """
        tkMessageBox.showerror(error_header, error_message)
        if move_frame:
            self.show_frame(frame)


class LoginPage(Frame):
    """The class of the login page"""

    def __init__(self, parent, controller):
        """Sets the initial variables and the page layout

        :param parent: the parent of the frame.
        :param controller: the main GUI class
        """
        Frame.__init__(self, parent)
        self.connected = False
        self.controller = controller
        login_label = Label(self, text="Login", font=self.controller.title_font)
        login_label.grid(column=0, row=0)

        self.user_label = Label(self, text="Username", font=("Arial", 12))
        self.user_label.grid(column=0, row=1)

        self.pass_label = Label(self, text="Password", font=("Arial", 12))
        self.pass_label.grid(column=0, row=2)

        self.user_text = Entry(self, width=20)
        self.user_text.grid(column=1, row=1)

        self.pass_text = Entry(self, width=20, show="*")
        self.pass_text.grid(column=1, row=2)

        self.login_button = Button(self, text="Login", command=self.check_login)
        self.login_button.grid(column=0, row=6)

        self.signup_button = Button(self, text="Sign Up", command=self.check_new_user)
        # self.signup_button.pack(side="bottom")
        self.signup_button.grid(column=1, row=6)
        self.pack()

    def check_connected(self):
        """Checks if the user is connected to the server. if not tries to connect."""
        if self.connected:
            return True
        else:
            self.connected = self.controller.client_side.run()
            return self.connected

    def check_login(self):
        """Tries to login to the server with the given username and password. if not raising an error message"""
        if self.check_connected():

            if self.controller.client_side.login(self.user_text.get(), self.pass_text.get()):
                tkMessageBox.showinfo("Login successfully",
                                      "You successfully logged in as {}".format(self.user_text.get()))
                self.controller.show_frame("FilePage")

    def check_new_user(self):
        """Tries to register and login to the server with the given username and password.
        if not raising an error message
        """
        if self.check_connected():

            if self.controller.client_side.new_user(self.user_text.get(), self.pass_text.get()):
                if self.controller.client_side.login(self.user_text.get(), self.pass_text.get()):
                    tkMessageBox.showinfo("Login successfully",
                                          "You successfully signed up and logged in")
                    self.controller.show_frame("FilePage")


class FilePage(Frame):
    """The class of the file page"""

    def __init__(self, parent, controller):
        """Sets the initial variables and the page layout

         :param parent: the parent of the frame.
         :param controller: the main GUI class
         """
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
        """Opens a file dialog and saves the chosen path both in a variable and to the config file."""
        file_path = tkFileDialog.askopenfilename(initialdir=self.last_opened)
        self.file_path_text.delete(0, END)
        self.file_path_text.insert(0, file_path)
        self.last_opened = "".join(file_path.split("/")[0:-1])
        self.controller.config.set("UI", "file_path", self.last_opened)

    def can_continue(self):
        """Updates the config file and checks the file. if the file is encrypted automatically moving to the decryption
        otherwise moving to the next page.
        """
        with open("SecuredEncryption.ini", 'wb') as c_file:
            self.controller.config.write(c_file)

        self.controller.file = self.file_path_text.get()
        if self.controller.client_side.check_enc_file(self.controller.file):
            tkMessageBox.showinfo("Encrypted file detected", "The file chosen is detected as an encrypted file. "
                                                             "moving to decryption")
            self.controller.frames["EncDecPage"].operation.set("decrypt")
            self.controller.frames["EncDecPage"].continue_next_page()
        else:
            self.controller.show_frame("EncDecPage")


class EncDecPage(Frame):
    """The class for the Operation choosing page."""

    def __init__(self, parent, controller):
        """Sets the initial variables and the page layout

         :param parent: the parent of the frame.
         :param controller: the main GUI class
         """
        Frame.__init__(self, parent)
        self.controller = controller

        self.operation = StringVar()
        self.operation.set("encrypt")
        self.type = StringVar()
        self.type.set("aes")

        label = Label(self, text="Choose a type of encryption", font=controller.title_font)
        label.grid(column=0, row=0)

        self.AES_radio = Radiobutton(self, text="AES", variable=self.type, value="aes", state="active")
        self.AES_radio.grid(column=0, row=1)

        self.Builtin_radio = Radiobutton(self, text="BlowFish", variable=self.type, value="blowfish", state="normal")
        self.Builtin_radio.grid(column=1, row=1)

        self.continue_button = Button(self, text="continue", command=self.continue_next_page)
        self.continue_button.grid(column=1, row=2)

        self.return_button = Button(self, text="back", command=self.return_page)
        self.return_button.grid(column=0, row=2)

    def return_page(self):
        """Returns the the previous page"""
        self.controller.show_frame("FilePage")

    def continue_next_page(self):
        """Continues to the next page and doing the chosen operation with the chosen type."""
        if self.operation.get() == "encrypt":
            completed = self.controller.client_side.encrypt(self.controller.file, self.type.get())
            if completed:
                tkMessageBox.showinfo("Encryption successful", "Finished encrypting the file. \n\r The encrypted file "
                                                               "path is '{}'".format(self.controller.file + ".jn"))
        else:
            completed = self.controller.client_side.decrypt(self.controller.file)
            if completed:
                tkMessageBox.showinfo("Decryption successful", "Finished decrypting the file. \n\r The decrypted file "
                                                               "path is '{}'".format(self.controller.file[:-3]))
        if completed:
            self.controller.show_frame("FinishPage")


class FinishPage(Frame):
    """The class for the finish page"""

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        label = Label(self, text="Finished", font=controller.title_font)
        label.grid(column=0, row=0)

        finish_button = Button(self, text="Choose new file", command=self.start_again)
        finish_button.grid(column=0, row=2)

        open_folder_button = Button(self, text="Open resulted file in explorer", command=self.open_directory)
        open_folder_button.grid(column=0, row=1)

        exit_button = Button(self, text="Exit", command=self.exit_ui)
        exit_button.grid(column=0, row=3)

    def open_directory(self):
        """Opens the resulted file directory"""
        try:
            path = "/".join(self.controller.file.split("/")[0:-1])
            print path
            os.startfile(path)
        except Exception:
            tkMessageBox.showerror("File error", "Could not find the folder '{}'".format(
                "".join(self.controller.file.split("/")[0:-1])))

    def start_again(self):
        """Going back to the file page"""
        self.controller.show_frame("FilePage")

    def exit_ui(self):
        """Exits the UI"""
        self.controller.client_side.exit()
        self.controller.destroy()


if __name__ == "__main__":
    app = GUIClass()
    app.mainloop()
