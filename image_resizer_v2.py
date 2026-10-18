import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageOps, ImageFilter
from tkinterdnd2 import DND_FILES, TkinterDnD

APP_TITLE = "画像かんたん変換 v2"

# 出力サイズは、よく使う用途向けの初期設定です。必要に応じて画面上で変更できます。
PRESETS = [
    {"name": "LANDR（正方形ジャケット）", "w": 1500, "h": 1500, "fmt": "JPG"},
    {"name": "Spotify（縦長）", "w": 900, "h": 1600, "fmt": "JPG"},
    {"name": "YouTubeショート（縦長）", "w": 1080, "h": 1920, "fmt": "JPG"},
    {"name": "YouTube横動画（16:9）", "w": 1920, "h": 1080, "fmt": "JPG"},
]
SUPPORTED = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")

class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("760x700")
        self.root.minsize(680, 620)
        self.files = []
        self.output_dir = tk.StringVar(value="")
        self.bg_color = "#202020"
        self.preset_vars = []
        self.format_vars = []
        self.size_vars = []

        outer = ttk.Frame(root, padding=14)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="画像かんたん変換", font=("", 17, "bold")).pack(anchor="w")
        ttk.Label(outer, text="画像をドラッグ＆ドロップで追加して用途を選ぶだけ。元画像は変更せず、用途別フォルダに保存します。").pack(anchor="w", pady=(2, 12))

        file_frame = ttk.LabelFrame(outer, text="1. 変換する画像", padding=10)
        file_frame.pack(fill="both", expand=True)
        btnrow = ttk.Frame(file_frame)
        btnrow.pack(fill="x", pady=(0, 6))
        ttk.Button(btnrow, text="画像を追加", command=self.add_files).pack(side="left")
        ttk.Button(btnrow, text="画像を削除", command=self.remove_selected).pack(side="left", padx=6)
        ttk.Button(btnrow, text="一覧をクリア", command=self.clear_files).pack(side="left")
        self.listbox = tk.Listbox(file_frame, height=7, selectmode=tk.EXTENDED)
        self.listbox.pack(fill="both", expand=True)
        # 画像ファイルをリストへドラッグ＆ドロップできるようにする
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind("<<Drop>>", self.drop_files)

        outrow = ttk.Frame(outer)
        outrow.pack(fill="x", pady=10)
        ttk.Label(outrow, text="保存先：").pack(side="left")
        self.out_label = ttk.Label(outrow, text="画像と同じ場所に保存", foreground="#555")
        self.out_label.pack(side="left", fill="x", expand=True)
        ttk.Button(outrow, text="保存先を選ぶ", command=self.choose_output).pack(side="right")

        preset_frame = ttk.LabelFrame(outer, text="2. 出力する用途（複数選択OK）", padding=10)
        preset_frame.pack(fill="x")
        for i, p in enumerate(PRESETS):
            row = ttk.Frame(preset_frame)
            row.pack(fill="x", pady=3)
            selected = tk.BooleanVar(value=True)
            self.preset_vars.append(selected)
            ttk.Checkbutton(row, text=p["name"], variable=selected, width=31).pack(side="left")
            wv, hv = tk.StringVar(value=str(p["w"])), tk.StringVar(value=str(p["h"]))
            self.size_vars.append((wv, hv))
            ttk.Label(row, text="幅").pack(side="left", padx=(6, 2))
            ttk.Entry(row, textvariable=wv, width=7).pack(side="left")
            ttk.Label(row, text="× 高さ").pack(side="left", padx=3)
            ttk.Entry(row, textvariable=hv, width=7).pack(side="left")
            fv = tk.StringVar(value=p["fmt"])
            self.format_vars.append(fv)
            ttk.Label(row, text="形式").pack(side="left", padx=(8, 2))
            ttk.Combobox(row, textvariable=fv, values=("JPG", "PNG", "WEBP"), state="readonly", width=6).pack(side="left")

        opts = ttk.LabelFrame(outer, text="3. 画像の合わせ方", padding=10)
        opts.pack(fill="x", pady=(10, 0))
        self.fit_mode = tk.StringVar(value="余白")
        ttk.Radiobutton(opts, text="切り抜かない（余白を付けて全体を残す）", variable=self.fit_mode, value="余白").pack(anchor="w")
        ttk.Radiobutton(opts, text="中央を切り抜いてサイズいっぱいにする", variable=self.fit_mode, value="切り抜き").pack(anchor="w")
        bgrow = ttk.Frame(opts)
        bgrow.pack(fill="x", pady=(5, 0))
        ttk.Label(bgrow, text="余白の背景色：").pack(side="left")
        self.bg_button = ttk.Button(bgrow, text="背景色を選ぶ（現在 #202020）", command=self.choose_bg)
        self.bg_button.pack(side="left")
        ttk.Label(bgrow, text="  ※JPGでは透明部分は背景色になります。").pack(side="left")

        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(12, 0))
        self.status = ttk.Label(bottom, text="準備完了")
        self.status.pack(side="left", fill="x", expand=True)
        ttk.Button(bottom, text="変換スタート", command=self.convert).pack(side="right", ipadx=14, ipady=5)

    def add_files(self):
        paths = filedialog.askopenfilenames(title="画像を選択", filetypes=[("画像ファイル", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("すべてのファイル", "*.*")])
        for path in paths:
            if path not in self.files and path.lower().endswith(SUPPORTED):
                self.files.append(path)
                self.listbox.insert(tk.END, path)

    def drop_files(self, event):
        try:
            paths = self.root.tk.splitlist(event.data)
        except Exception:
            paths = [event.data]
        added = 0
        for path in paths:
            path = path.strip()
            if os.path.isfile(path) and path.lower().endswith(SUPPORTED) and path not in self.files:
                self.files.append(path)
                self.listbox.insert(tk.END, path)
                added += 1
        self.status.config(text=f"ドラッグ＆ドロップで {added} 個の画像を追加しました" if added else "追加できる画像がありませんでした")
        return "break"

    def remove_selected(self):
        indices = list(self.listbox.curselection())
        for i in reversed(indices):
            self.listbox.delete(i)
            del self.files[i]

    def clear_files(self):
        self.files.clear()
        self.listbox.delete(0, tk.END)

    def choose_output(self):
        path = filedialog.askdirectory(title="保存先フォルダーを選択")
        if path:
            self.output_dir.set(path)
            self.out_label.config(text=path)

    def choose_bg(self):
        result = colorchooser.askcolor(color=self.bg_color, title="余白の背景色を選択")
        if result and result[1]:
            self.bg_color = result[1]
            self.bg_button.config(text=f"背景色を選ぶ（現在 {self.bg_color}）")

    def make_canvas(self, img, w, h):
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGBA")
        if self.fit_mode.get() == "切り抜き":
            fitted = ImageOps.fit(img, (w, h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            return fitted.convert("RGB") if self.current_format == "JPG" else fitted
        # 余白モード：全体を収め、指定サイズのキャンバスに配置。画像は切り抜かない。
        thumb = ImageOps.contain(img, (w, h), method=Image.Resampling.LANCZOS)
        if self.current_format == "JPG":
            canvas = Image.new("RGB", (w, h), self.bg_color)
            if thumb.mode == "RGBA":
                canvas.paste(thumb, ((w-thumb.width)//2, (h-thumb.height)//2), thumb.getchannel("A"))
            else:
                canvas.paste(thumb.convert("RGB"), ((w-thumb.width)//2, (h-thumb.height)//2))
            return canvas
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        canvas.alpha_composite(thumb, ((w-thumb.width)//2, (h-thumb.height)//2))
        return canvas

    def convert(self):
        if not self.files:
            messagebox.showinfo("画像がありません", "先に画像を追加してください。")
            return
        selected_presets = []
        for i, p in enumerate(PRESETS):
            if self.preset_vars[i].get():
                try:
                    w, h = int(self.size_vars[i][0].get()), int(self.size_vars[i][1].get())
                    if w < 1 or h < 1 or w > 20000 or h > 20000:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("サイズエラー", f"{p['name']} の幅・高さを正しく入力してください（1$301C20000）。")
                    return
                fmt = self.format_vars[i].get().upper()
                selected_presets.append((p["name"], w, h, fmt))
        if not selected_presets:
            messagebox.showinfo("用途が未選択", "出力する用途にチェックを入れてください。")
            return
        errors, done = [], 0
        for source in self.files:
            try:
                with Image.open(source) as original:
                    for name, w, h, fmt in selected_presets:
                        self.current_format = fmt
                        result = self.make_canvas(original.copy(), w, h)
                        if fmt == "JPG":
                            if result.mode not in ("RGB", "L"):
                                result = result.convert("RGB")
                            ext, save_format = ".jpg", "JPEG"
                            save_options = {"quality": 95, "optimize": True}
                        elif fmt == "PNG":
                            if result.mode not in ("RGBA", "RGB", "L"):
                                result = result.convert("RGBA")
                            ext, save_format = ".png", "PNG"
                            save_options = {"optimize": True}
                        else:
                            if result.mode not in ("RGBA", "RGB", "L"):
                                result = result.convert("RGBA")
                            ext, save_format = ".webp", "WEBP"
                            save_options = {"quality": 95, "method": 6}
                        stem = os.path.splitext(os.path.basename(source))[0]
                        safe_name = name.split("（")[0].split("（")[0].replace(" ", "_")
                        # 保存先の中に「画像変換済み」フォルダを作り、用途別に整理して保存
                        base_folder = self.output_dir.get() or os.path.dirname(source)
                        output_root = os.path.join(base_folder, "画像変換済み")
                        preset_folder_names = {
                            "LANDR": "LANDR",
                            "Spotify": "Spotify",
                            "YouTubeショート": "YouTubeショート",
                            "YouTube横動画": "YouTube横動画",
                        }
                        preset_folder = preset_folder_names.get(name.split("（")[0], safe_name)
                        folder = os.path.join(output_root, preset_folder)
                        os.makedirs(folder, exist_ok=True)
                        outpath = os.path.join(folder, f"{stem}_{w}x{h}{ext}")
                        result.save(outpath, format=save_format, **save_options)
                        done += 1
            except Exception as e:
                errors.append(f"{os.path.basename(source)}：{e}")
        self.status.config(text=f"完了：{done} 個の画像を保存しました")
        if errors:
            messagebox.showwarning("一部変換できませんでした", f"{done} 個を保存しました。\n\n" + "\n".join(errors[:8]))
        else:
            messagebox.showinfo("変換完了", f"{done} 個の画像を保存しました。\n元画像は変更していません。")

def main():
    root = TkinterDnD.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
