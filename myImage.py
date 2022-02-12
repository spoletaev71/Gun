from tkinter import *
from PIL import ImageTk, Image

root = Tk()
root.geometry('1024x768')
pilImage = Image.open("ScreenBG01_new.jpg")
image = ImageTk.PhotoImage(pilImage)
canvas = Canvas(root, width=pilImage.size[0], height=pilImage.size[1])
imagesprite = canvas.create_image(0, 0, anchor=NW, image=image)
canvas.pack(expand=1, fill=BOTH)
root.mainloop()
