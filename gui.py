from tkinter import Tk, Button, Canvas
from PIL import Image, ImageTk

class Window:
    def __init__(self, master, img_paths):
        self.master = master

        self.img_before = None
        self.img_after = None
        self.button = None

        self._draw_images(img_paths)
        self._create_buttons()

    def _draw_images(self, img_paths):
        self.img_before = ImageTk.PhotoImage(Image.open(img_paths[0]))
        self.img_after = ImageTk.PhotoImage(Image.open(img_paths[1]))

        self.cv = Canvas(self.master, width=512 * 2, height=512)
        self.cv.pack(side='top', fill='both', expand='yes')
        self.cv.create_image(0, 0, image=self.img_before, anchor='nw')

        self.cv.move(self.img_before, 512, 0)
        self.cv.create_image(512, 0, image=self.img_after, anchor='nw')

    def _create_button(self, text, command):
        self.button = Button(self.master, text=text, command=command)
        self.button.pack(side='left')

    def _create_buttons(self):
        self._create_button(text="Add constraint point", command=self.test)
        self._create_button(text="Hide constraints points", command=self.test)
        self._create_button(text="Show constraints points", command=self.test)
        self._create_button(text="Start morphing", command=self.test)
        self._create_button(text="<< Frame", command=self.test)
        self._create_button(text="Frame >>", command=self.test)
        self._create_button(text="Close program", command=self.master.quit)

    def test(self):
        pass

root = Tk()
my_gui = Window(root, img_paths=("before.jpg", "after.jpg"))
root.mainloop()