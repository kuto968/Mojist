import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import tkinter.font as tkfont
import os
from pathlib import Path
import traceback
import sys
import json
class MojistApp:
    def __init__(self, root):
        self.root = root
        
        self.BASE_DIR = self._get_base_dir()
        self.BG_FOLDER = self.BASE_DIR / "Image"
        self.ICON_PATH = self.BASE_DIR / "assets" / "favicon.ico"
        self.PROJECTS_FOLDER = self.BASE_DIR / "Projects"
        self.BG_FOLDER.mkdir(exist_ok=True)
        self.ICON_PATH.parent.mkdir(exist_ok=True)
        self.PROJECTS_FOLDER.mkdir(exist_ok=True)
        self.THUMBNAIL_SIZE = (160, 90)
        self.THUMBS_PER_PAGE = 9

        self.image = None
        self.photo = None
        self.font_list = sorted(f for f in tkfont.families() if "@" not in f)
        self.selected_font_name = self._get_initial_font()
        self.font_size = 50
        self.text_color = "white"
        self.outline_color = "black"
        self.outline_width = 2
        self.x, self.y = 512, 502
        self.adjust_x, self.adjust_y = self.x, self.y

        self.fixed_text = None
        self.preset_text = None

        self.repeat_job = None

        self.adjust_window = None
        self.preset_edit_window = None
        self.background_selector_window = None
        self.adjust_initial_text_color = ""
        self.adjust_initial_outline_color = ""
        self.adjust_initial_outline_width = 0 
        self.adjust_initial_font_size = 0 
        self.adjust_step = tk.IntVar(value=1) 
        
        self.bg_image_files = []
        self.bg_total_pages = 1
        self.bg_current_page = 0
        self.bg_selected_index = None
        self.bg_thumbs = [] 

        self._setup_window()
        self._create_widgets()
        self._load_initial_image()
        self.update_text()

    def _get_base_dir(self):
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        else:
            return Path(__file__).resolve().parent

    def _get_initial_font(self):
        preferred_fonts = ["Meiryo", "MS UI Gothic", "Yu Gothic UI", "MS Gothic"]
        return next((f for f in preferred_fonts if f in self.font_list), self.font_list[0])

    def _setup_window(self):
        self.root.title("Mojist")
        self.root.geometry("1024x640")
        self.root.resizable(False, False)
        self.root.bind("<Button-1>", self._on_window_click)

    def _load_initial_image(self):
        image_path = self.BG_FOLDER / "P000.png"
        try:
            if image_path.exists():
                self.apply_background_image(image_path)
            else:
                raise FileNotFoundError("初期画像が存在しません。")
        except Exception as e:
            print(f"初期画像読み込み失敗: {e}")
            self.image = Image.new("RGB", (1024, 576), color=(128, 128, 128))
            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

    def _create_widgets(self):
        control_area = tk.Frame(self.root)
        control_area.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        top_frame = tk.Frame(control_area)
        top_frame.pack(fill=tk.X)

        self.input_text = tk.Entry(top_frame, font=("M PLUS 1p Medium", 20))
        self.input_text.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.input_text.bind("<Return>", lambda event: self.toggle_fixed_text())

        self.font_combo = ttk.Combobox(top_frame, values=self.font_list, state="readonly", width=20)
        self.font_combo.set(self.selected_font_name)
        self.font_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.font_combo.bind("<<ComboboxSelected>>", self.change_font)
        
        bottom_frame = tk.Frame(control_area)
        bottom_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Button(bottom_frame, text="反映", command=self.toggle_fixed_text).pack(side=tk.LEFT)
        separator1 = ttk.Separator(bottom_frame, orient='vertical')
        separator1.pack(side=tk.LEFT, fill='y', padx=10, pady=5)
        tk.Button(bottom_frame, text="プリセット登録", command=self.register_preset).pack(side=tk.LEFT)
        self.preset_display_button = tk.Button(bottom_frame, text="プリセットなし", bg="#f0f0f0", cursor="hand2")
        self.preset_display_button.pack(side=tk.LEFT, padx=5)
        self.preset_display_button.bind("<Double-Button-1>", lambda e: self.open_preset_edit_window())
        tk.Button(bottom_frame, text="プリセット反映", command=self.reflect_preset).pack(side=tk.LEFT)
        separator2 = ttk.Separator(bottom_frame, orient='vertical')
        separator2.pack(side=tk.LEFT, fill='y', padx=10, pady=5)
        tk.Button(bottom_frame, text="総合調整", command=self.open_adjust_window).pack(side=tk.LEFT)
        tk.Button(bottom_frame, text="背景変更", command=self.open_background_selector).pack(side=tk.LEFT, padx=5)
        separator3 = ttk.Separator(bottom_frame, orient='vertical')
        separator3.pack(side=tk.LEFT, fill='y', padx=10, pady=5)
        tk.Button(bottom_frame, text="保存", command=self._save_project).pack(side=tk.LEFT)
        tk.Button(bottom_frame, text="呼び出し", command=self._load_project).pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW)

    def update_text(self):
        self.canvas.itemconfig(self.canvas_image, image=self.photo)
        self.canvas.delete("text")
        main_text = self.fixed_text if self.fixed_text else self.input_text.get() or "文字"
        self.draw_text(self.x, self.y, main_text)

    def draw_text(self, x, y, text):
        font_tuple = (self.selected_font_name, self.font_size, "bold")
        offset = self.outline_width

        if offset > 0:
            for dx in range(-offset, offset + 1):
                for dy in range(-offset, offset + 1):
                    if dx**2 + dy**2 <= offset**2:
                        self.canvas.create_text(x + dx, y + dy, text=text, font=font_tuple, fill=self.outline_color, tags="text")
                        
        self.canvas.create_text(x, y, text=text, font=font_tuple, fill=self.text_color, tags="text")

    def toggle_fixed_text(self):
        self.fixed_text = self.input_text.get()
        self.update_text()

    def change_font(self, event=None):
        self.selected_font_name = self.font_combo.get()
        self.update_text()
        
    def _on_window_click(self, event):
        if event.widget not in (self.input_text, self.font_combo):
            self.root.focus_set()

    def register_preset(self):
        text = self.input_text.get()
        if len(text) > 100:
            print("プリセット登録文字数が多すぎます。100文字以内にしてください。")
            return
        self.preset_text = text
        self.show_preset()

    def reflect_preset(self):
        if self.preset_text:
            self.fixed_text = self.preset_text
            self.update_text()

    def show_preset(self):
        display_text = self.preset_text if self.preset_text else "プリセットなし"
        if len(display_text) > 15:
            display_text = display_text[:15] + "..."
        self.preset_display_button.config(text=display_text)

    def open_preset_edit_window(self):
        if self.preset_text is None:
            return
        if self.preset_edit_window and self.preset_edit_window.winfo_exists():
            self.preset_edit_window.lift()
            return

        self.preset_edit_window = tk.Toplevel(self.root)
        self.preset_edit_window.title("プリセット編集")
        self.preset_edit_window.protocol("WM_DELETE_WINDOW", self.close_preset_edit)

        tk.Label(self.preset_edit_window, text="プリセットを編集:").pack(pady=(10, 0))
        edit_entry = tk.Entry(self.preset_edit_window, font=("M PLUS 1p Medium", 20), width=30)
        edit_entry.insert(0, self.preset_text)
        edit_entry.pack(padx=20, pady=(0, 10))

        button_frame = tk.Frame(self.preset_edit_window)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="キャンセル", width=10, command=self.close_preset_edit).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="反映", width=10, command=lambda: self.apply_preset_edit(edit_entry)).pack(side=tk.RIGHT, padx=10)

    def close_preset_edit(self):
        if self.preset_edit_window and self.preset_edit_window.winfo_exists():
            self.preset_edit_window.destroy()
        self.preset_edit_window = None

    def apply_preset_edit(self, entry):
        self.preset_text = entry.get()
        self.show_preset()
        self.close_preset_edit()

    def open_adjust_window(self):
        """総合調整ウィンドウを開く"""
        if self.adjust_window and self.adjust_window.winfo_exists():
            self.adjust_window.lift()
            return

        self.adjust_x, self.adjust_y = self.x, self.y
        self.adjust_initial_font_size = self.font_size
        self.adjust_initial_text_color = self.text_color
        self.adjust_initial_outline_color = self.outline_color
        self.adjust_initial_outline_width = self.outline_width

        self.adjust_window = tk.Toplevel(self.root)
        self.adjust_window.title("総合調整")
        self.adjust_window.geometry("400x300")
        self.adjust_window.resizable(False, False)
        self.adjust_window.protocol("WM_DELETE_WINDOW", self._cancel_adjustments)
        self.adjust_window.grab_set()

        main_pane = tk.Frame(self.adjust_window)
        main_pane.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        left_frame = tk.Frame(main_pane, width=120, bd=2, relief="ridge")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False)

        self.right_frame = tk.Frame(main_pane)
        self.right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        tk.Button(left_frame, text="位置調整", command=lambda: self._switch_adjust_panel("position")).pack(fill=tk.X, pady=5, padx=5)
        tk.Button(left_frame, text="サイズ調整", command=lambda: self._switch_adjust_panel("size")).pack(fill=tk.X, pady=5, padx=5)
        tk.Button(left_frame, text="色の調整", command=lambda: self._switch_adjust_panel("color")).pack(fill=tk.X, pady=5, padx=5)
        tk.Button(left_frame, text="縁の調整", command=lambda: self._switch_adjust_panel("outline")).pack(fill=tk.X, pady=5, padx=5)

        self.adjust_panels = {
            "position": self._create_position_panel(self.right_frame),
            "size": self._create_size_panel(self.right_frame),
            "color": self._create_color_panel(self.right_frame),
            "outline": self._create_outline_panel(self.right_frame)
        }
        
        button_frame = tk.Frame(self.adjust_window)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        tk.Button(button_frame, text="キャンセル", width=10, command=self._cancel_adjustments).pack(side=tk.RIGHT, padx=10)
        tk.Button(button_frame, text="決定", width=10, command=self._confirm_adjustments).pack(side=tk.RIGHT)

        self._switch_adjust_panel("position")

    def _switch_adjust_panel(self, panel_name):
        for name, panel in self.adjust_panels.items():
            if name == panel_name:
                panel.pack(expand=True, fill=tk.BOTH)
            else:
                panel.pack_forget()

    def _create_position_panel(self, parent):
        panel = tk.Frame(parent)

        step_frame = tk.LabelFrame(panel, text="移動ステップ数", padx=10, pady=5)
        step_frame.pack(pady=10, padx=10, fill="x")
        steps = [1, 5, 10]
        for step in steps:
            rb = tk.Radiobutton(step_frame, text=f"{step}px", variable=self.adjust_step, value=step)
            rb.pack(side=tk.LEFT, padx=15, expand=True)

        control = tk.Frame(panel)
        control.pack(pady=10, padx=10)

        up_btn = tk.Button(control, text="↑", width=4)
        left_btn = tk.Button(control, text="←", width=4)
        right_btn = tk.Button(control, text="→", width=4)
        down_btn = tk.Button(control, text="↓", width=4)

        up_btn.grid(row=0, column=1)
        left_btn.grid(row=1, column=0)
        right_btn.grid(row=1, column=2)
        down_btn.grid(row=2, column=1)

        up_btn.bind("<ButtonPress-1>", lambda e, dx=0, dy=-1: self._start_move(dx, dy))
        left_btn.bind("<ButtonPress-1>", lambda e, dx=-1, dy=0: self._start_move(dx, dy))
        right_btn.bind("<ButtonPress-1>", lambda e, dx=1, dy=0: self._start_move(dx, dy))
        down_btn.bind("<ButtonPress-1>", lambda e, dx=0, dy=1: self._start_move(dx, dy))

        up_btn.bind("<ButtonRelease-1>", self._stop_move)
        left_btn.bind("<ButtonRelease-1>", self._stop_move)
        right_btn.bind("<ButtonRelease-1>", self._stop_move)
        down_btn.bind("<ButtonRelease-1>", self._stop_move)

        return panel

    def _create_size_panel(self, parent):
        panel = tk.Frame(parent, padx=10, pady=10)
        
        size_label_frame = tk.Frame(panel)
        size_label_frame.pack(fill=tk.X, pady=5)

        tk.Label(size_label_frame, text="フォントサイズ:").pack(side=tk.LEFT)
        self.size_value_label = tk.Label(size_label_frame, text=str(self.font_size), font=("", 10, "bold"))
        self.size_value_label.pack(side=tk.LEFT)

        size_scale = tk.Scale(
            panel, from_=10, to=200,
            orient=tk.HORIZONTAL,
            showvalue=0,
            command=self._change_font_size_from_slider
        )
        size_scale.set(self.font_size)
        size_scale.pack(expand=True, fill=tk.X)
        return panel

    def _create_color_panel(self, parent):
        """「色の調整」用のパネルを作成する"""
        from tkinter.colorchooser import askcolor

        panel = tk.Frame(parent, padx=10, pady=10)

        text_color_frame = tk.Frame(panel)
        text_color_frame.pack(fill=tk.X, pady=5)
        tk.Button(text_color_frame, text="文字色", width=10, command=self._choose_text_color).pack(side=tk.LEFT)
        self.text_color_preview = tk.Frame(text_color_frame, width=100, height=25, bg=self.text_color, relief="sunken", bd=1)
        self.text_color_preview.pack(side=tk.LEFT, padx=10)

        outline_color_frame = tk.Frame(panel)
        outline_color_frame.pack(fill=tk.X, pady=5)
        tk.Button(outline_color_frame, text="縁の色", width=10, command=self._choose_outline_color).pack(side=tk.LEFT)
        self.outline_color_preview = tk.Frame(outline_color_frame, width=100, height=25, bg=self.outline_color, relief="sunken", bd=1)
        self.outline_color_preview.pack(side=tk.LEFT, padx=10)

        return panel

    def _create_outline_panel(self, parent):
        panel = tk.Frame(parent, padx=10, pady=10)
        
        label_frame = tk.Frame(panel)
        label_frame.pack(fill=tk.X, pady=5)

        tk.Label(label_frame, text="縁の太さ:").pack(side=tk.LEFT)
        self.outline_width_label = tk.Label(label_frame, text=str(self.outline_width), font=("", 10, "bold"))
        self.outline_width_label.pack(side=tk.LEFT)

        width_scale = tk.Scale(
            panel, from_=0, to=10,
            orient=tk.HORIZONTAL,
            showvalue=0,
            command=self._change_outline_width_from_slider
        )
        width_scale.set(self.outline_width)
        width_scale.pack(expand=True, fill=tk.X)
        return panel

    def _change_outline_width_from_slider(self, new_width_str):
        new_width = int(float(new_width_str))
        self.outline_width = new_width
        self.outline_width_label.config(text=str(new_width))
        self.update_text()

    def _choose_text_color(self):
        from tkinter.colorchooser import askcolor
        color_code = askcolor(title="文字色を選択", initialcolor=self.text_color)
        if color_code[1]:
            self.text_color = color_code[1]
            self.text_color_preview.config(bg=self.text_color)
            self.update_text()

    def _choose_outline_color(self):
        from tkinter.colorchooser import askcolor
        color_code = askcolor(title="縁の色を選択", initialcolor=self.outline_color)
        if color_code[1]:
            self.outline_color = color_code[1]
            self.outline_color_preview.config(bg=self.outline_color)
            self.update_text()

    def _move_text(self, dx, dy):
        step = self.adjust_step.get()
        self.x += dx * step
        self.y += dy * step
        self.update_text()
    
    def _start_move(self, dx, dy):
        self._move_text(dx, dy)
        self.repeat_job = self.root.after(500, self._repeat_move, dx, dy)

    def _repeat_move(self, dx, dy):
        self._move_text(dx, dy)
        self.repeat_job = self.root.after(100, self._repeat_move, dx, dy)

    def _stop_move(self, event):
        if self.repeat_job:
            self.root.after_cancel(self.repeat_job)
            self.repeat_job = None

    def _change_font_size_from_slider(self, new_size_str):
        new_size = int(float(new_size_str))
        self.font_size = new_size
        self.size_value_label.config(text=str(new_size))
        self.update_text()

    def _confirm_adjustments(self):
        if self.adjust_window and self.adjust_window.winfo_exists():
            self.adjust_window.grab_release()
            self.adjust_window.destroy()
        self.adjust_window = None

    def _cancel_adjustments(self):
        self.x, self.y = self.adjust_x, self.adjust_y
        self.font_size = self.adjust_initial_font_size
        self.text_color = self.adjust_initial_text_color
        self.outline_color = self.adjust_initial_outline_color
        self.outline_width = self.adjust_initial_outline_width

        self.update_text()
        self._confirm_adjustments()

    def open_background_selector(self):
        if self.background_selector_window and self.background_selector_window.winfo_exists():
            self.background_selector_window.lift()
            return

        self.background_selector_window = tk.Toplevel(self.root)
        self.background_selector_window.title("背景変更")
        self.background_selector_window.geometry("600x500")
        self.background_selector_window.resizable(False, False)
        self.background_selector_window.protocol("WM_DELETE_WINDOW", self._close_background_selector)
        self.background_selector_window.grab_set()

        control_frame = tk.Frame(self.background_selector_window)
        control_frame.pack(pady=5)
        tk.Button(control_frame, text="←", command=lambda: self._change_bg_page(-1)).pack(side=tk.LEFT)
        self.page_label = tk.Label(control_frame, text="1 / 1")
        self.page_label.pack(side=tk.LEFT, padx=10)
        tk.Button(control_frame, text="→", command=lambda: self._change_bg_page(1)).pack(side=tk.LEFT)

        tk.Button(self.background_selector_window, text="🔄 再読み込み", command=lambda: self._draw_bg_page(force_reload=True)).pack(pady=5)
        
        self.grid_frame = tk.Frame(self.background_selector_window)
        self.grid_frame.pack()

        tk.Button(self.background_selector_window, text="決定", command=self._apply_background_selection).pack(side=tk.RIGHT, padx=10, pady=10)

        self._draw_bg_page(force_reload=True)

    def _draw_bg_page(self, force_reload=False):
        if force_reload:
            self.bg_image_files = sorted([f for f in self.BG_FOLDER.iterdir() if f.suffix.lower() in (".png", ".jpg", ".jpeg")])
            self.bg_total_pages = (len(self.bg_image_files) - 1) // self.THUMBS_PER_PAGE + 1
            if self.bg_total_pages == 0: self.bg_total_pages = 1
            self.bg_current_page = min(self.bg_current_page, self.bg_total_pages - 1)

        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.bg_thumbs.clear()

        start = self.bg_current_page * self.THUMBS_PER_PAGE
        end = start + self.THUMBS_PER_PAGE
        for i, img_path in enumerate(self.bg_image_files[start:end]):
            try:
                img = Image.open(img_path).resize(self.THUMBNAIL_SIZE)
                thumb = ImageTk.PhotoImage(img)
                self.bg_thumbs.append(thumb)
            except Exception as e:
                print(f"サムネイル生成失敗: {img_path.name}\n{traceback.format_exc()}")
                continue

            frame = tk.Frame(self.grid_frame, bd=2, relief="solid", highlightthickness=0)
            if self.bg_selected_index == start + i:
                frame.config(highlightbackground="#008000", highlightthickness=2)

            img_label = tk.Label(frame, image=thumb, cursor="hand2")
            img_label.pack()
            tk.Label(frame, text=img_path.name, wraplength=self.THUMBNAIL_SIZE[0]).pack()
            frame.grid(row=i // 3, column=i % 3, padx=5, pady=5)
            
            img_label.bind("<Button-1>", lambda e, idx=start + i: self._select_bg(idx))
        
        self.page_label.config(text=f"{self.bg_current_page + 1} / {self.bg_total_pages}")
    
    def _select_bg(self, index):
        self.bg_selected_index = index
        self._draw_bg_page()

    def _change_bg_page(self, delta):
        new_page = self.bg_current_page + delta
        if 0 <= new_page < self.bg_total_pages:
            self.bg_current_page = new_page
            self._draw_bg_page()

    def _apply_background_selection(self):
        if self.bg_selected_index is not None:
            selected_file_path = self.bg_image_files[self.bg_selected_index]
            try:
                self.apply_background_image(selected_file_path)
            except Exception as e:
                print(f"背景画像の適用に失敗しました: {e}\n{traceback.format_exc()}")
        self._close_background_selector()

    def _close_background_selector(self):
        if self.background_selector_window and self.background_selector_window.winfo_exists():
            self.background_selector_window.grab_release()
            self.background_selector_window.destroy()
        self.background_selector_window = None

    def apply_background_image(self, path):
        from tkinter import messagebox

        self.image_path = path

        try:
            self.image = Image.open(path).resize((1024, 576))
            self.photo = ImageTk.PhotoImage(self.image)
            self.update_text()
        except Exception as e:
            error_detail = traceback.format_exc()
            messagebox.showerror(
                "画像読み込みエラー",
                f"背景画像の読み込みに失敗しました。\n\nファイル: {path.name}\n詳細: {e}"
            )
            print(error_detail)

            self.image = Image.new("RGB", (1024, 576), color=(128, 128, 128))
            self.photo = ImageTk.PhotoImage(self.image)
            self.update_text()

    def _save_project(self):
        project_data = {
            "text": self.input_text.get(),
            "font_name": self.selected_font_name,
            "font_size": self.font_size,
            "text_color": self.text_color,
            "outline_color": self.outline_color,
            "outline_width": self.outline_width,
            "x": self.x,
            "y": self.y,
            "background_image_path": str(getattr(self, 'image_path', ''))
        }

        file_path = filedialog.asksaveasfilename(
            initialdir=self.PROJECTS_FOLDER,
            title="プロジェクトを保存",
            filetypes=(("JSONファイル", "*.json"), ("すべてのファイル", "*.*")),
            defaultextension=".json"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("保存完了", f"プロジェクトを保存しました。\n{Path(file_path).name}")
        except Exception as e:
            messagebox.showerror("保存エラー", f"プロジェクトの保存に失敗しました。\n\n詳細: {e}")

    def _load_project(self):
        file_path = filedialog.askopenfilename(
            initialdir=self.PROJECTS_FOLDER,
            title="プロジェクトを呼び出し",
            filetypes=(("JSONファイル", "*.json"), ("すべてのファイル", "*.*"))
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.fixed_text = data.get("text", "文字")
            self.input_text.delete(0, tk.END)
            self.input_text.insert(0, self.fixed_text)
            
            self.selected_font_name = data.get("font_name", self._get_initial_font())
            self.font_combo.set(self.selected_font_name)

            self.font_size = data.get("font_size", 50)
            self.text_color = data.get("text_color", "white")
            self.outline_color = data.get("outline_color", "black")
            self.outline_width = data.get("outline_width", 2)
            self.x = data.get("x", 512)
            self.y = data.get("y", 502)

            bg_path_str = data.get("background_image_path")
            if bg_path_str:
                bg_path = Path(bg_path_str)
                if bg_path.exists():
                    self.apply_background_image(bg_path)
                else:
                    messagebox.showwarning("警告", f"背景画像が見つかりませんでした。\n{bg_path_str}")
            
            self.update_text()
            messagebox.showinfo("読み込み完了", f"プロジェクトを読み込みました。\n{Path(file_path).name}")

        except Exception as e:
            messagebox.showerror("読み込みエラー", f"プロジェクトの読み込みに失敗しました。\n\n詳細: {e}")

if __name__ == '__main__':
    root = tk.Tk()
    app = MojistApp(root)
    root.mainloop()
