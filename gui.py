"""

imgwriter / gui.py
Copyright (c) 2022 Pyry Lahtinen
https://github.com/PyryL/imgwriter
File created on 2022-08-20

"""

from tkinter import Tk, Label, Entry, StringVar, Button, Radiobutton, scrolledtext, WORD, Frame, Checkbutton, IntVar, INSERT, Message
from tkinter.ttk import Notebook
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import showerror, showinfo
from main import Writer, Reader
import os

class GUI(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ImgWriter")
        self.resizable(False, False)

        notebook = Notebook(self)
        notebook.grid(column=0, row=0, padx=10, pady=10)
        writeTab, readTab, infoTab = WriteView(notebook), ReadView(notebook), InfoView(notebook)
        notebook.add(writeTab, text="Write")
        notebook.add(readTab, text="Read")
        notebook.add(infoTab, text="About")


class WriteView(Frame):
    def __init__(self, root) -> None:
        super().__init__(root)

        # image file input
        self.__imageInput = FileWidget(self, "Image file:", ("PNG image file", "*.png"))
        self.__imageInput.grid(column=0, row=0, columnspan=2)

        # payload input type
        self.__payloadTypeTextvar = StringVar(value="plain")
        self.__payloadTypeTextvar.trace("w", self.__payloadTypeChanged)
        Radiobutton(self, text="Plain text input", variable=self.__payloadTypeTextvar, value="plain").grid(column=0, row=1)
        Radiobutton(self, text="File input", variable=self.__payloadTypeTextvar, value="file").grid(column=1, row=1)

        # plain text input
        self.__plainTextInput = scrolledtext.ScrolledText(self, wrap=WORD, width=30, height=10)
        
        # file text input
        self.__payloadFileInput = FileWidget(self, "Payload file:")
        self.__payloadTypeChanged()

        # include exif
        self.__exifSelection = IntVar()
        Checkbutton(self, text="Modify EXIF", variable=self.__exifSelection, onvalue=1, offvalue=0).grid(column=0, row=3, columnspan=2)

        Button(self, text="Run", command=self.__submit).grid(column=0, row=4, columnspan=2)
    
    def __payloadTypeChanged(self, *args) -> None:
        if self.__payloadTypeTextvar.get() == "plain":
            self.__plainTextInput.grid(column=0, row=2, columnspan=2)
            self.__payloadFileInput.grid_remove()
        else:
            self.__payloadFileInput.grid(column=0, row=2, columnspan=2)
            self.__plainTextInput.grid_remove()
    
    def __extractFileExtension(self, path: str) -> str:
        """ returns the file extension of the path, or None is such doesn't exist """
        filename = os.path.split(path)[1]
        if "." not in filename or filename.rfind(".") == 0: return None
        return filename.split(".")[-1]

    def __submit(self) -> None:
        # get input image
        imageFile = self.__imageInput.filename
        if "/" not in imageFile:
            showerror("Invalid input image", "Please select an input image first")
            return
        if not os.path.exists(imageFile):
            showerror("File not found", f"Image file {imageFile} not found")
            return

        # get payload
        if self.__payloadTypeTextvar.get() == "plain": 
            payload = self.__plainTextInput.get("1.0", "end-1c").encode("utf-8")
            dataType = "txt"
            if len(payload) == 0:
                showerror("Empty payload", "Please give some payload first")
                return
        else:
            if "/" not in self.__payloadFileInput.filename:
                showerror("No payload file", "Please select a payload file first")
                return
            try:
                with open(self.__payloadFileInput.filename, "rb") as file:
                    payload = file.read()
            except FileNotFoundError:
                showerror("File not found", f"Payload file {self.__payloadFileInput.filename} not found")
                return
            dataType = self.__extractFileExtension(self.__payloadFileInput.filename)
        
        # get exif selection
        addExif = self.__exifSelection.get() == 1

        # perform writing
        try:
            writer = Writer(imageFile, payload, dataType)
        except Exception as e:
            showerror("An error occurred", f"An error occurred during the process:{os.linesep}{e}")
            return
        
        # save the output
        pngFileType = ("PNG image file", "*.png")
        filename = asksaveasfilename(filetypes=[pngFileType], defaultextension=[pngFileType])
        if filename == "": return
        if not filename.lower().endswith(".png"):
            showerror("Not a PNG file", "Please save the output image as PNG")
            return
        writer.save(filename, addExif)
        showinfo("File saved", f"Image has been saved to {filename}")


class ReadView(Frame):
    def __init__(self, root) -> None:
        super().__init__(root)

        self.__imageInput = FileWidget(self, "Image file:", ("PNG image file", "*.png"))
        self.__imageInput.grid(column=0, row=0, columnspan=2)

        Button(self, text="Read to text", command=self.__readText).grid(column=0, row=1)
        Button(self, text="Read to file", command=self.__readFile).grid(column=1, row=1)

        self.__plainTextOutput = scrolledtext.ScrolledText(self, wrap=WORD, width=30, height=10)
        self.__plainTextOutput.grid(column=0, row=2, columnspan=2)
        self.__setPlainTextOutput("")       # disable textfield
    
    def __setPlainTextOutput(self, value: str) -> None:
        self.__plainTextOutput.configure(state="normal")
        self.__plainTextOutput.insert(INSERT, value)
        self.__plainTextOutput.configure(state="disabled")
    
    def __performRead(self) -> Reader:
        # get image
        imageFilename = self.__imageInput.filename
        if "/" not in imageFilename:
            showerror("Invalid input image", "Please select an input image first")
            return None
        if not os.path.exists(imageFilename):
            showerror("File not found", f"Image file {imageFilename} not found")
            return None
        try:
            return Reader(imageFilename)
        except Exception as e:
            showerror("Error occurred", f"An error occurred during the process:{os.linesep}{e}")

    def __readText(self) -> None:
        reader = self.__performRead()
        if reader == None: return
        self.__setPlainTextOutput(reader.payloadBinary.decode("utf-8"))

    def __readFile(self) -> None:
        # perform the reading
        reader = self.__performRead()
        if reader == None: return

        # output
        self.__setPlainTextOutput("")
        fileTypeOption = [("Original file type", f"*.{reader.dataType}"), ("All files", "*.*")]
        filename = asksaveasfilename(filetypes=fileTypeOption, defaultextension=fileTypeOption)
        if filename == "": return
        with open(filename, "wb") as file:
            file.write(reader.payloadBinary)
        showinfo("File saved", f"Image contents have been saved to {filename}")


class InfoView(Frame):
    def __init__(self, root) -> None:
        super().__init__(root)

        Label(self, text="ImgWriter", font=(None, 20, "bold")).grid(column=0, row=0)

        Label(self, text="Version 1.0", fg="gray").grid(column=0, row=1)

        infoText = [
            "Store data inside images.",
            "Copyright (c) 2022 Pyry Lahtinen",
            "https://github.com/PyryL/imgwriter",
            "For legal purposes only."
        ]
        Message(self, text=os.linesep.join(infoText), width=300).grid(column=0, row=2)


class FileWidget(Frame):
    def __init__(self, root, label, fileType: tuple[str, str] = ("All files", "*.*"), **kw) -> None:
        super().__init__(root, **kw)
        self.__fileType = fileType
        self.__filename = ""
        self.__uiFilename = StringVar(value="Not selected")
        Label(self, text=label).grid(column=0, row=0)
        Button(self, text="Select", command=self.__selectFile).grid(column=1, row=0)
        Label(self, textvariable=self.__uiFilename).grid(column=2, row=0)
    
    def __selectFile(self) -> None:
        filename = askopenfilename(filetypes=[self.__fileType], defaultextension=[self.__fileType])
        if filename == () or filename == "": return
        self.__filename = filename

        uiFilename = os.path.split(filename)[1]
        uiFilename = uiFilename if len(uiFilename) <= 18 else uiFilename[:9]+"..."+uiFilename[-9:]
        self.__uiFilename.set(uiFilename)
    
    @property
    def filename(self) -> str:
        return self.__filename


if __name__ == "__main__":
    GUI().mainloop()
