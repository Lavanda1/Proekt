import tkinter as tk
from tkinter import colorchooser, messagebox, filedialog
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

# Для фигур
shape_start_x = None
shape_start_y = None
shape_preview = None

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


def clear_current_layer():
    """Очищает текущий активный слой"""
    if messagebox.askyesno("Очистка слоя", f"Вы действительно хотите очистить слой {active_layer_index + 1}?"):
        save_history()
        # Создаем новый пустой слой (полностью прозрачный)
        layers[active_layer_index] = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        rebuild_drawers()
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
tk.Button(layer_panel, text="🧹 Очистить слой", command=clear_current_layer).pack(fill=tk.X, pady=2)

# КНОПКИ СЛЕВА
tool_panel = tk.Frame(root)
tool_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5)

def set_mode(m):
    global mode, shape_start_x, shape_start_y
    mode = m
    shape_start_x = None
    shape_start_y = None
    # Очищаем предпросмотр при смене инструмента
    if shape_preview:
        canvas.delete(shape_preview)

# Функция сохранения (определяем ДО того, как используем)
def save_image():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[
            ("PNG файлы", "*.png"),
            ("JPEG файлы", "*.jpg"),
            ("Все файлы", "*.*")
        ]
    )

    if file_path:
        final_image = Image.new("RGB", (CANVAS_W, CANVAS_H), "white")
        for i, layer in enumerate(layers):
            if layers_visibility[i]:
                final_image.paste(layer, (0, 0), layer)

        final_image.save(file_path)
        messagebox.showinfo("Сохранено", f"Изображение сохранено как:\n{file_path}")

# ФУНКЦИИ ДЛЯ ФИГУР
def draw_rectangle(draw, x1, y1, x2, y2, color, width):
    """Рисует прямоугольник (только контур) с заданной толщиной"""
    left, top = min(x1, x2), min(y1, y2)
    right, bottom = max(x1, x2), max(y1, y2)
    draw.rectangle([left, top, right, bottom], outline=color, width=width)

def draw_line(draw, x1, y1, x2, y2, color, width):
    """Рисует линию с заданной толщиной"""
    draw.line([x1, y1, x2, y2], fill=color, width=width)

def draw_circle(draw, x1, y1, x2, y2, color, width):
    """Рисует круг (только контур) с заданной толщиной"""
    # Находим центр и радиус
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    radius = max(abs(x2 - x1), abs(y2 - y1)) // 2

    left = center_x - radius
    right = center_x + radius
    top = center_y - radius
    bottom = center_y + radius

    draw.ellipse([left, top, right, bottom], outline=color, width=width)

# Обработка рисования фигур
def start_shape(e):
    global shape_start_x, shape_start_y, shape_preview
    if mode in ["rectangle", "line", "circle"]:
        shape_start_x = e.x
        shape_start_y = e.y
        # Удаляем старый предпросмотр
        if shape_preview:
            canvas.delete(shape_preview)

def draw_shape_preview(e):
    global shape_preview, shape_start_x, shape_start_y
    if shape_start_x is not None and mode in ["rectangle", "line", "circle"]:
        # Удаляем старый предпросмотр
        if shape_preview:
            canvas.delete(shape_preview)

        # Толщина предпросмотра зависит от размера кисти
        preview_width = brush_size

        # Создаем новый предпросмотр в зависимости от фигуры
        if mode == "rectangle":
            shape_preview = canvas.create_rectangle(shape_start_x, shape_start_y, e.x, e.y,
                                                    outline=current_color, width=preview_width, fill="")
        elif mode == "line":
            shape_preview = canvas.create_line(shape_start_x, shape_start_y, e.x, e.y,
                                               fill=current_color, width=preview_width)
        elif mode == "circle":
            shape_preview = canvas.create_oval(shape_start_x, shape_start_y, e.x, e.y,
                                               outline=current_color, width=preview_width, fill="")

def finish_shape(e):
    global shape_start_x, shape_start_y, shape_preview
    if shape_start_x is not None and mode in ["rectangle", "line", "circle"]:
        save_history()

        # Рисуем фигуру на слое
        draw = layers_draw[active_layer_index]
        color_rgb = current_color

        # Используем размер кисти для толщины линий
        line_width = brush_size

        if mode == "rectangle":
            draw_rectangle(draw, shape_start_x, shape_start_y, e.x, e.y, color_rgb, line_width)
        elif mode == "line":
            draw_line(draw, shape_start_x, shape_start_y, e.x, e.y, color_rgb, line_width)
        elif mode == "circle":
            draw_circle(draw, shape_start_x, shape_start_y, e.x, e.y, color_rgb, line_width)

        # Очищаем предпросмотр
        if shape_preview:
            canvas.delete(shape_preview)
            shape_preview = None
        shape_start_x = None
        shape_start_y = None

        update_canvas()

# КНОПКИ ИНСТРУМЕНТОВ
for name, m in [
    ("Кисть", "brush"),
    ("Ластик", "eraser"),
    ("Заливка", "fill"),
    ("Пипетка", "picker"),
    ("Прямоугольник", "rectangle"),
    ("Линия", "line"),
    ("Круг", "circle"),
]:
    tk.Button(tool_panel, text=name, width=14, command=lambda m=m: set_mode(m)).pack(pady=2)

tk.Button(tool_panel, text="💾 Сохранить", width=14, command=save_image).pack(pady=2)
tk.Button(tool_panel, text="⬅ назад", command=lambda: undo()).pack(pady=10)
tk.Button(tool_panel, text="➡ вперед", command=lambda: redo()).pack()

# ВЕРХНЯЯ ПАНЕЛЬ
top = tk.Frame(root)
top.pack(side=tk.TOP, fill=tk.X)

tk.Label(top, text="Кисть").pack(side=tk.LEFT)
brush_scale = tk.Scale(top, from_=1, to=80, orient=tk.HORIZONTAL,
                       command=lambda v: globals().__setitem__("brush_size", int(v)))
brush_scale.set(brush_size)
brush_scale.pack(side=tk.LEFT)

# Показываем текущий размер кисти
brush_size_label = tk.Label(top, text=f"Размер: {brush_size}", width=10)
brush_size_label.pack(side=tk.LEFT, padx=5)


def update_brush_size(v):
    brush_size = int(v)
    brush_size_label.config(text=f"Размер: {brush_size}")
    globals().__setitem__("brush_size", brush_size)

brush_scale.config(command=update_brush_size)

tk.Label(top, text="Ластик").pack(side=tk.LEFT)
eraser_scale = tk.Scale(top, from_=1, to=80, orient=tk.HORIZONTAL,
                        command=lambda v: globals().__setitem__("eraser_size", int(v)))
eraser_scale.set(eraser_size)
eraser_scale.pack(side=tk.LEFT)

# Показываем текущий размер ластика
eraser_size_label = tk.Label(top, text=f"Размер: {eraser_size}", width=10)
eraser_size_label.pack(side=tk.LEFT, padx=5)

def update_eraser_size(v):
    eraser_size = int(v)
    eraser_size_label.config(text=f"Размер: {eraser_size}")
    globals().__setitem__("eraser_size", eraser_size)

eraser_scale.config(command=update_eraser_size)


def choose_color():
    global current_color
    c = colorchooser.askcolor()[1]
    if c:
        current_color = c
        color_preview.config(bg=c)

tk.Button(top, text="Цвет", command=choose_color).pack(side=tk.LEFT, padx=5)
color_preview = tk.Label(top, bg=current_color, width=3)
color_preview.pack(side=tk.LEFT)

# ПИПЕТКА - выбор цвета с холста
def pick_color(e):
    global current_color, mode
    img = layers[active_layer_index]

    if 0 <= e.x < CANVAS_W and 0 <= e.y < CANVAS_H:
        pixel = img.getpixel((e.x, e.y))

        if len(pixel) == 4:
            hex_color = f"#{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}"
        else:
            hex_color = f"#{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}"

        current_color = hex_color
        color_preview.config(bg=current_color)
        mode = "brush" #<- АВТОМАТИЧЕСКИ ВОЗВРАЩАЕМСЯ НА КИСТЬ

# ЗАЛИВКА
def flood_fill(x, y):
    save_history()
    img = layers[active_layer_index]
    px = img.load()
    w, h = img.size

    target = px[x, y]
    fill_color = Image.new("RGBA", (1, 1), current_color).getpixel((0, 0))

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
            (cx + 1, cy), (cx - 1, cy),
            (cx, cy + 1), (cx, cy - 1)
        ])
    update_canvas()

# РИСОВАНИЕ КИСТЬЮ
def smooth_line(x0, y0, x1, y1, color, r):
    dx, dy = x1-x0, y1-y0
    steps = max(abs(dx), abs(dy), 1)
    for i in range(steps):
        x = int(x0+dx*i/steps)
        y = int(y0+dy*i/steps)
        layers_draw[active_layer_index].ellipse(
            [x-r, y-r, x+r, y+r], fill=color, outline=color
        )

def draw(e):
    global last_x, last_y

    # Для фигур используем отдельную обработку
    if mode in ["rectangle", "line", "circle"]:
        return  # Фигуры обрабатываются в start_shape, draw_shape_preview, finish_shape

    if mode == "picker":
        pick_color(e)
        return

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
        smooth_line(last_x, last_y, e.x, e.y, (0, 0, 0, 0), eraser_size//2)

    last_x, last_y = e.x, e.y
    update_canvas()

def reset(_):
    global last_x, last_y
    last_x = last_y = None

# Привязываем события для фигур и обычного рисования
canvas.bind("<Button-1>", lambda e: start_shape(e) if mode in ["rectangle", "line", "circle"] else draw(e))
canvas.bind("<B1-Motion>", lambda e: draw_shape_preview(e) if mode in ["rectangle", "line", "circle"] else draw(e))
canvas.bind("<ButtonRelease-1>", lambda e: finish_shape(e) if mode in ["rectangle", "line", "circle"] else reset(e))


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