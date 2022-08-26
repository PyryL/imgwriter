"""

imgwriter / cli.py
Copyright (c) 2022 Pyry Lahtinen
https://github.com/PyryL/imgwriter
File created on 2022-08-20

"""

from main import Writer, Reader
import argparse
import os
import json
from base64 import b64encode

class App:
    def __init__(self) -> None:
        self.__parseArguments()
        try:
            self.__decideReadWrite()
            if self.__isWriteMode: self.__performWrite()
            else: self.__performRead()
        except Exception as e:
            self.__handleError(3, str(e))

    def __parseArguments(self) -> None:
        desc = os.linesep.join([
            "Store data inside images",
            "Copyright (c) 2022 Pyry Lahtinen",
            "https://github.com/PyryL/imgwriter",
            "For legal purposes only."
        ])
        parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)

        parser.add_argument("image", help="The image containing data")
        parser.add_argument("-i", action="store_true", help="Overwrite the original image (with -t and -f)")
        parser.add_argument("-e", action="store_true", help="Add imgwriter to image's exif data (with -t and -f)")
        parser.add_argument("-s", action="store_true", help="Silent mode")
        parser.add_argument("-m", action="store_true", help="Machine readable mode")

        # write arguments
        storeDataGroup = parser.add_mutually_exclusive_group()
        storeDataGroup.add_argument("-t", metavar="TEXT", help="Store text inside the image")
        storeDataGroup.add_argument("-f", metavar="PATH", help="Store contents of file inside the image")

        # read arguments
        readDataGroup = parser.add_mutually_exclusive_group()
        readDataGroup.add_argument("-p", action="store_true", help="Print the image content to terminal")
        readDataGroup.add_argument("-o", metavar="PATH", help="Save the image content to file")

        self.__args = vars(parser.parse_args())
        self.__silentMode = self.__args["s"] == True
        self.__machineMode = self.__args["m"] == True

    def __extractFileExtension(self, path: str) -> str:
        """ returns the file extension of the path, or None if such doesn't exist """
        filename = os.path.split(path)[1]
        if "." not in filename or filename.rfind(".") == 0: return None
        return filename.split(".")[-1]

    def __handleError(self, errorCode: int, description: str) -> None:
        """ Print error details in wanted format and exit """
        if type(errorCode) != int or type(description) != str:
            raise ValueError()

        if self.__machineMode and not self.__silentMode:
            print(json.dumps({
                "error": errorCode,
                "description": description
            }))
        elif not self.__silentMode:
            print(description)
        exit(errorCode)

    def __decideReadWrite(self) -> None:
        """ Decide whether should read or write data """
        if self.__args["t"] is not None or self.__args["f"] is not None:
            self.__isWriteMode = True
        elif self.__args["p"] == True or self.__args["o"] is not None:
            self.__isWriteMode = False
        else:
            self.__handleError(1, "Neither read nor write options provided. Pass -t, -f, -p or -o, or --help to learn more.")
    
    def __addFileNameComponent(self, filename: str, component: str) -> str:
        """
        Adds a component to the end of the filename
        Example: "test.png" + "foobar" -> "test.foobar.png"
        abc.pyry.def.png
        """
        path, file = os.path.split(filename)
        if "." in file: file = ".".join(file.split(".")[:-1]) + "." + component + "." + file.split(".")[-1]
        else: file += "_" + component
        return os.path.join(path, file)

    def __performWrite(self) -> None:
        # get payload
        if self.__args["t"] is not None:
            payload = str(self.__args["t"]).encode("utf-8")
            dataType = "txt"
        else:
            try:
                with open(self.__args["f"], "rb") as file: payload = file.read()
                dataType = self.__extractFileExtension(self.__args["f"])
            except FileNotFoundError:
                self.__handleError(2, f"File '{self.__args['f']}' not found")
        
        # come up with the saving filename
        if self.__args["i"] == True: savingFilename = self.__args["image"]
        else: savingFilename = self.__addFileNameComponent(self.__args["image"], "data")
        
        # write payload and save
        addExif = self.__args["e"] == True
        Writer(self.__args["image"], payload, dataType).save(savingFilename, addExif)

        if self.__machineMode and not self.__silentMode:
            print(json.dumps({
                "success": True,
                "path": os.path.abspath(savingFilename)
            }))
        elif not self.__silentMode:
            print(f"Writing done and image saved to '{savingFilename}'")

    def __performRead(self) -> None:
        # get the payload from image
        payload = Reader(self.__args["image"]).payloadBinary

        # handle the payload
        if self.__args["p"] == True:
            # convert payload bytes to str
            try: payloadStr = (payload.decode("utf-8"), False)
            except UnicodeDecodeError: payloadStr = (b64encode(payload).decode("utf-8"), True)

            if self.__machineMode:
                objectToPrint = {"success": True, "payload": payloadStr[0]}
                if payloadStr[1]: objectToPrint["base64"] = True
                print(json.dumps(objectToPrint))
            else:
                if payloadStr[1]: print(f"NOTE: Here is the base64 encoded representation of {len(payload)} original bytes")
                print(payloadStr[0])
        else:
            with open(self.__args["o"], "wb") as file:
                file.write(payload)
            if self.__machineMode:
                print(json.dumps({
                    "success": True,
                    "path": os.path.abspath(self.__args["o"])
                }))
            else:
                print(f"Data read and saved to '{self.__args['o']}'")

if __name__ == "__main__":
    App()
