from sys import argv
from copy import copy
from threading import Thread
from PIL import Image, ImageTk
from tkinter import Tk, Button, Canvas, TclError

from triangles import Triangles


class Window:
    def __init__(self, master, img_paths):
        """
        Beforehand initial images and 2 triangles are drawn, buttons are created
        """
        self.master = master
        self.binded = None
        self.show = True
        self.prev = None
        self.frames_number = 16
        self.created_items = []
        self.created_images = []

        self.triangles = Triangles()
        self._draw_images(img_paths)
        self._draw_triangles()
        self._create_buttons()

    def _draw_images(self, img_paths):
        """
        Just creating Canvas entity with two side by side images
        """
        self.img_before = Image.open(img_paths[0])
        self.img_after = Image.open(img_paths[1])
        self.original = copy(self.img_before)

        self.tk_img_before = ImageTk.PhotoImage(self.img_before)
        self.tk_img_after = ImageTk.PhotoImage(self.img_after)

        self.cv = Canvas(self.master, width=512 * 2, height=512)
        self.cv.pack(side='top', fill='both', expand='yes')
        self.created_images.append(
            self.cv.create_image(0, 0, image=self.tk_img_before, anchor='nw')
        )

        self.cv.move(self.tk_img_before, 512, 0)
        self.cv.create_image(512, 0, image=self.tk_img_after, anchor='nw')

    def _create_button(self, text, command):
        """
        Function for creating button with text on it;
        After pressing the button the command will be executed
        """
        self.button = Button(self.master, text=text, command=command)
        self.button.pack(side='left')

    def _create_frame_button(self):
        """
        Button, which does nothing, just for visualizing number of frames
        :return:
        """
        self.frames_button = Button(self.master,
                                    text="{} Frames".format(self.frames_number),
                                    command=self.try_unbind())
        self.frames_button.pack(side='left')

    def _create_buttons(self):
        """
        All buttons' creating
        """
        self._create_button(text="Add constraint point", command=self._detect_points)
        self._create_button(text="Hide constraints points", command=self._hide_points)
        self._create_button(text="Show constraints points", command=self._show_points)
        self._create_button(text="Start morphing", command=self._morphing)
        self._create_button(text=" << ", command=self._decrease_frames)
        self._create_frame_button()
        self._create_button(text=" >> ", command=self._increase_frames)
        self._create_button(text="Close program", command=self.master.quit)

    def callback(self, event):
        """
        Event after double pressing on images
        """
        if self.prev is None:
            self.prev = (event.x, event.y)
        else:
            self.triangles.add_point(self.prev, (event.x, event.y))
            self.prev = None

        if self.show:
            while self.created_items:
                item = self.created_items.pop()
                self.cv.delete(item)
            self._draw_triangles()

    def _detect_points(self):
        """
        Trying to detect points to be constraint points
        """
        self.prev = None
        self.binded = self.master.bind("<Double-Button-1>", self.callback)

    def _draw_point(self, coord):
        """
        Visualising points
        """
        x, y = coord
        self.created_items.append(
            self.cv.create_oval(x, y, x + 1, y + 1, fill="#476042")
        )
        self.cv.pack()

    def _draw_line(self, pt1, pt2):
        """
        Visualising line with begin (pt1) and end (pt2)
        All entities are adding to self.created_items for future delete (if user wants to hide)
        """
        self.created_items.append(
            self.cv.create_line(pt1[0], pt1[1], pt2[0], pt2[1])
        )
        self.cv.pack()

    def _draw_triangle(self, triangle):
        """
        Draw triangle as 3 lines
        """
        for i, point in enumerate(triangle):
            self._draw_point(point)
            if i != 2:
                self._draw_line(triangle[i], triangle[i+1])
        self._draw_line(triangle[2], triangle[0])

    def _draw_triangles(self):
        """
        Draw all triangles
        """
        for end, start in self.triangles.match.items():
            self._draw_triangle(end)
            self._draw_triangle(start)

    def _hide_points(self):
        """
        Hidding constraint points as deleting lines and points which were created
        """
        self.try_unbind()
        if self.show:
            self.show = False

        while self.created_items:
            item = self.created_items.pop()
            self.cv.delete(item)

    def _show_points(self):
        """
        Show constraint points as creating triangles
        :return:
        """
        self.try_unbind()
        if self.show:
            return
        self.show = True
        self._draw_triangles()

    def _increase_frames(self):
        """
        Increasing number of frames
        """
        self.try_unbind()
        self.frames_number = min(4096, self.frames_number * 2)
        self.frames_button['text'] = "{} Frames".format(self.frames_number)

    def _decrease_frames(self):
        """
        Decreasing number of frames
        """
        self.try_unbind()
        self.frames_number = max(2, self.frames_number // 2)
        self.frames_button['text'] = "{} Frames".format(self.frames_number)

    def _frame_update(self, tau):
        """
        Cycle for morphing visualization
        Call determine_coords from Triangles class
        """
        for i in range(self.frames_number):
            self.img_before = self.triangles.determine_coords(self.original,
                                                              self.img_after,
                                                              i * tau)
            self.tk_img_before = ImageTk.PhotoImage(self.img_before)
            self.cv.delete(self.created_images[-1])
            self.cv.create_image(0, 0, image=self.tk_img_before, anchor='nw')
            self._draw_triangles()

    def _morphing(self):
        """
        Call of morphing
        """
        self.try_unbind()
        tau = 1 / self.frames_number
        thread = Thread(target=self._frame_update, args=(tau,))
        thread.start()

    def try_unbind(self):
        try:
            self.master.unbind("<Double-Button-1>", self.binded)
        except TclError:
            pass

if __name__ == "__main__":
    if len(argv) != 3:
        print("You need to provide 2 directories!")
        exit(0)

    root = Tk()
    my_gui = Window(root, img_paths=(argv[1], argv[2]))
    root.mainloop()
