# Small TKinter program to assist in creating various simulation components
# Mostly for use in debugging

import tkinter as tk

# -- EDITOR SUBWINDOWS --
class MemberEditor(tk.Frame):
    def __init__(self, parent):
        self.pack()

        self.label = tk.Label(text="hello world")
        self.label.pack()

class Editor(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()

        self.master.title("Battlematus State Editor")
        self.master.geometry("800x600")

        self.entrythingy = tk.Entry()
        self.entrythingy.pack()

        # Create the application variable.
        self.contents = tk.StringVar()
        # Set it to some value.
        self.contents.set("this is a variable")
        # Tell the entry widget to watch this variable.
        self.entrythingy["textvariable"] = self.contents

        # Define a callback for when the user hits return.
        # It prints the current value of the variable.
        self.entrythingy.bind('<Key-Return>',
                             self.print_contents)
        
        self.test = tk.Frame(bg="black", width=100, height=100)
        self.test.pack()

    def print_contents(self, event):
        print("Hi. The current entry content is:",
              self.contents.get())


def startEditor():
    root = tk.Tk()
    myapp = Editor(root)
    myapp.mainloop()

if __name__ == "__main__":
    startEditor()