from tkinter import Tk, Button, Canvas, TclError
from PIL import Image, ImageTk
from triangles import Trianles

class Window:
    def __init__(self, master, img_paths):
        self.master = master

        self.img_before = None
        self.img_after = None
        self.button = None
        self.binded = None
        self.show = True
        self.prev = None
        self.created_items = []

        self.triangles = Trianles()
        self._draw_images(img_paths)
        self._draw_triangles()
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
        self._create_button(text="Add constraint point", command=self._detect_points)
        self._create_button(text="Hide constraints points", command=self.hide_points)
        self._create_button(text="Show constraints points", command=self.show_points)
        self._create_button(text="Start morphing", command=self.try_unbind)
        self._create_button(text="<< Frame", command=self.try_unbind)
        self._create_button(text="Frame >>", command=self.try_unbind)
        self._create_button(text="Close program", command=self.master.quit)

    def callback(self, event):
        if self.prev is None:
            self.prev = (event.x, event.y)
        else:
            self.triangles.add_point(self.prev, (event.x, event.y))
            self.prev = None

        if self.show:
            self._draw_triangles()

    def _detect_points(self):
        self.binded = self.master.bind("<Double-Button-1>", self.callback)

    def _draw_point(self, coord):
        x, y = coord
        self.created_items.append(
            self.cv.create_oval(x, y, x + 1, y + 1, fill="#476042")
        )
        self.cv.pack()

    def _draw_line(self, pt1, pt2):
        self.created_items.append(
            self.cv.create_line(pt1[0], pt1[1], pt2[0], pt2[1])
        )
        self.cv.pack()

    def _draw_triangle(self, triangle):
        for i, point in enumerate(triangle):
            self._draw_point(point)
            if i != 2:
                self._draw_line(triangle[i], triangle[i+1])
        self._draw_line(triangle[2], triangle[0])

    def _draw_triangles(self):
        for end, start in self.triangles.end.items():
            self._draw_triangle(end)
            self._draw_triangle(start)

    def hide_points(self):
        self.try_unbind()
        if self.show:
            self.show = False

        while self.created_items:
            item = self.created_items.pop()
            self.cv.delete(item)

    def show_points(self):
        if self.show:
            return
        self.show = True
        self._draw_triangles()

    def try_unbind(self):
        try:
            self.master.unbind("<Double-Button-1>", self.binded)
        except TclError:
            pass

root = Tk()
my_gui = Window(root, img_paths=("before.jpg", "after.jpg"))
root.mainloop()