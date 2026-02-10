import tkinter as tk
from tkinter import colorchooser, messagebox
from PIL import Image, ImageDraw, ImageTk
import copy
from collections import deque

# ОКНО ПРОГРАМЫ
root = tk.Tk()
root.title("MyPaint — Layers Pro")
root.geometry("1100x720")

CANVAS_W, CANVAS_H = 850, 650

# СОСТОЯНИЕ
current_color = "#000000"
brush_size = 5
eraser_size = 20
mode = "brush"
last_x = last_y = None
active_layer_index = 0

# СЛОИ
layers = []
layers_draw = []
layers_visibility = []

history = []
redo_stack = []

def save_history():
    history.append([copy.deepcopy(l) for l in layers])
    redo_stack.clear()

def rebuild_drawers():
    global layers_draw
    layers_draw = [ImageDraw.Draw(l) for l in layers]

# ХОЛСТ
canvas = tk.Canvas(root, bg="white", width=CANVAS_W, height=CANVAS_H)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

tk_image = ImageTk.PhotoImage(Image.new("RGB", (CANVAS_W, CANVAS_H), "white"))
canvas_img = canvas.create_image(0, 0, anchor="nw", image=tk_image)

def update_canvas():
    base = Image.new("RGB", (CANVAS_W, CANVAS_H), "white")
    for i, layer in enumerate(layers):
        if layers_visibility[i]:
            base.paste(layer, (0, 0), layer)
    global tk_image
    tk_image = ImageTk.PhotoImage(base)
    canvas.itemconfig(canvas_img, image=tk_image)

# СЛОИ: ЛОГИКА
def add_layer():
    global active_layer_index
    save_history()
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    layers.append(img)
    layers_visibility.append(True)
    rebuild_drawers()
    active_layer_index = len(layers) - 1
    update_layer_list()
    update_canvas()

def delete_layer():
    global active_layer_index
    if len(layers) <= 1:
        messagebox.showinfo("Нельзя", "Должен остаться хотя бы один слой")
        return
    save_history()
    layers.pop(active_layer_index)
    layers_visibility.pop(active_layer_index)
    rebuild_drawers()
    active_layer_index = max(0, active_layer_index - 1)
    update_layer_list()
    update_canvas()

def move_layer_up():
    global active_layer_index
    if active_layer_index <= 0:
        return
    save_history()
    i = active_layer_index
    layers[i], layers[i-1] = layers[i-1], layers[i]
    layers_visibility[i], layers_visibility[i-1] = layers_visibility[i-1], layers_visibility[i]
    rebuild_drawers()
    active_layer_index -= 1
    update_layer_list()
    update_canvas()

def move_layer_down():
    global active_layer_index
    if active_layer_index >= len(layers) - 1:
        return
    save_history()
    i = active_layer_index
    layers[i], layers[i+1] = layers[i+1], layers[i]
    layers_visibility[i], layers_visibility[i+1] = layers_visibility[i+1], layers_visibility[i]
    rebuild_drawers()
    active_layer_index += 1
    update_layer_list()
    update_canvas()

def toggle_layer_visibility():
    idx = layer_listbox.curselection()
    if idx:
        i = idx[0]
        layers_visibility[i] = not layers_visibility[i]
        update_layer_list()
        update_canvas()

# СЛОИ И КНОПКИ
layer_panel = tk.Frame(root)
layer_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

tk.Label(layer_panel, text="Слои").pack()

layer_listbox = tk.Listbox(layer_panel, width=20)
layer_listbox.pack()

def update_layer_list():
    layer_listbox.delete(0, tk.END)
    for i, vis in enumerate(layers_visibility):
        marker = "👁️" if vis else "🚫"
        layer_listbox.insert(tk.END, f"{marker} Слой {i+1}")
    layer_listbox.selection_set(active_layer_index)

def select_layer(e):
    global active_layer_index
    sel = layer_listbox.curselection()
    if sel:
        active_layer_index = sel[0]

layer_listbox.bind("<<ListboxSelect>>", select_layer)

tk.Button(layer_panel, text="➕ Добавить", command=add_layer).pack(fill=tk.X)
tk.Button(layer_panel, text="🗑 Удалить", command=delete_layer).pack(fill=tk.X)
tk.Button(layer_panel, text="⬆ Вверх", command=move_layer_up).pack(fill=tk.X)
tk.Button(layer_panel, text="⬇ Вниз", command=move_layer_down).pack(fill=tk.X)
tk.Button(layer_panel, text="👁 Вкл/Выкл", command=toggle_layer_visibility).pack(fill=tk.X)

# КНОПКИ СЛЕВА
tool_panel = tk.Frame(root)
tool_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5)

def set_mode(m):
    global mode
    mode = m

for name, m in [
    ("Кисть", "brush"),
    ("Ластик", "eraser"),
    ("Заливка", "fill"),
]:
    tk.Button(tool_panel, text=name, width=14, command=lambda m=m: set_mode(m)).pack(pady=2)

tk.Button(tool_panel, text="⬅ назад", command=lambda: undo()).pack(pady=10)
tk.Button(tool_panel, text="➡ вперед", command=lambda: redo()).pack()

# ВЕРХНЯЯ ПАНЕЛЬ
top = tk.Frame(root)
top.pack(side=tk.TOP, fill=tk.X)

tk.Label(top, text="Кисть").pack(side=tk.LEFT)
tk.Scale(top, from_=1, to=80, orient=tk.HORIZONTAL,
         command=lambda v: globals().__setitem__("brush_size", int(v))).pack(side=tk.LEFT)

tk.Label(top, text="Ластик").pack(side=tk.LEFT)
tk.Scale(top, from_=1, to=80, orient=tk.HORIZONTAL,
         command=lambda v: globals().__setitem__("eraser_size", int(v))).pack(side=tk.LEFT)

def choose_color():
    global current_color
    c = colorchooser.askcolor()[1]
    if c:
        current_color = c
        color_preview.config(bg=c)

tk.Button(top, text="Цвет", command=choose_color).pack(side=tk.LEFT, padx=5)
color_preview = tk.Label(top, bg=current_color, width=3)
color_preview.pack(side=tk.LEFT)

# ЗАЛИВКА
def flood_fill(x, y):
    save_history()
    img = layers[active_layer_index]
    px = img.load()
    w, h = img.size

    target = px[x, y]
    fill_color = ImageColor = Image.new("RGBA", (1, 1), current_color).getpixel((0, 0))

    if target == fill_color:
        return

    q = deque()
    q.append((x, y))

    while q:
        cx, cy = q.popleft()
        if cx < 0 or cy < 0 or cx >= w or cy >= h:
            continue
        if px[cx, cy] != target:
            continue

        px[cx, cy] = fill_color

        q.extend([
            (cx+1, cy), (cx-1, cy),
            (cx, cy+1), (cx, cy-1)
        ])

    update_canvas()

# РИСОВАНИЕ
def smooth_line(x0, y0, x1, y1, color, r):
    dx, dy = x1-x0, y1-y0
    steps = max(abs(dx), abs(dy), 1)
    for i in range(steps):
        x = int(x0 + dx*i/steps)
        y = int(y0 + dy*i/steps)
        layers_draw[active_layer_index].ellipse(
            [x-r, y-r, x+r, y+r], fill=color, outline=color
        )

def draw(e):
    global last_x, last_y

    if mode == "fill":
        flood_fill(e.x, e.y)
        return

    if last_x is None:
        last_x, last_y = e.x, e.y
        save_history()
        return

    if mode == "brush":
        smooth_line(last_x, last_y, e.x, e.y, current_color, brush_size//2)
    elif mode == "eraser":
        smooth_line(last_x, last_y, e.x, e.y, (0,0,0,0), eraser_size//2)

    last_x, last_y = e.x, e.y
    update_canvas()

def reset(_):
    global last_x, last_y
    last_x = last_y = None

canvas.bind("<B1-Motion>", draw)
canvas.bind("<ButtonRelease-1>", reset)
canvas.bind("<Button-1>", draw)

# UNDO(вперед)/ REDO(назад)
def undo():
    global layers
    if history:
        redo_stack.append([copy.deepcopy(l) for l in layers])
        layers = history.pop()
        rebuild_drawers()
        update_canvas()

def redo():
    global layers
    if redo_stack:
        history.append([copy.deepcopy(l) for l in layers])
        layers = redo_stack.pop()
        rebuild_drawers()
        update_canvas()

add_layer()
root.mainloop()