import tkinter as tk
from tkinter import colorchooser

# окно программы
root = tk.Tk()
root.title("MyPaint")
root.geometry("900x650")

# состояние по умолчанию
current_color = "black" # текуший цвет кисти
brush_size = 5
eraser_size = 20
mode = "brush"

# холст и его цвет
canvas = tk.Canvas(root, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)


def set_color():
    global current_color, mode
    color = colorchooser.askcolor()[1]
    if color:
        current_color = color
        mode = "brush"  # переключаемся на кисть после выбора цвета


def activate_brush():
    global mode
    mode = "brush"

# включаем ластик
def activate_eraser():
    global mode
    mode = "eraser"

#изменение размера кисти
def change_brush_size(value):
    global brush_size
    brush_size = int(value)

#тут размер ластика
def change_eraser_size(value):
    global eraser_size
    eraser_size = int(value)


def draw(event):
    x, y = event.x, event.y

    if mode == "brush":
        size = brush_size
        color = current_color
    else:
        size = eraser_size
        color = "white"

    canvas.create_oval( x - size, y - size, x + size, y + size, fill=color, outline=color)

panel = tk.Frame(root)
panel.pack(fill=tk.X)

# кнопки
tk.Button(panel, text="Кисть", command=activate_brush).pack(side=tk.LEFT)
tk.Button(panel, text="Выбрать цвет", command=set_color).pack(side=tk.LEFT)
tk.Button(panel, text="Ластик", command=activate_eraser).pack(side=tk.LEFT)

# Размер ластика и кисти
brush_label = tk.Label(panel, text="Размер кисти:")
brush_label.pack(side=tk.LEFT, padx=5)
brush_slider = tk.Scale(panel, from_=1, to=100, orient=tk.HORIZONTAL, command=change_brush_size)
brush_slider.set(brush_size)
brush_slider.pack(side=tk.LEFT)

eraser_label = tk.Label(panel, text=" Размер ластика:")
eraser_label.pack(side=tk.LEFT, padx=5)
eraser_slider = tk.Scale(panel, from_=1, to=100, orient=tk.HORIZONTAL, command=change_eraser_size)
eraser_slider.set(eraser_size)
eraser_slider.pack(side=tk.LEFT)

# назначение рисовние на мышке
canvas.bind("<B1-Motion>", draw)

root.mainloop()
