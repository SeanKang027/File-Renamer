import ctypes
import json
import os
import re
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    import customtkinter as ctk
except ImportError:
    root = tk.Tk(); root.withdraw()
    messagebox.showerror("缺少套件", "File Renamer 需要 CustomTkinter。\n\n請先執行：\npip install customtkinter")
    root.destroy(); sys.exit(1)

APP_NAME = "File Renamer"
APP_VERSION = "1.6.1"

def get_app_data_dir():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    app_dir = base / "FileRenamer"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

def resource_path(name):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name

HISTORY_FILE = get_app_data_dir() / "rename_history.json"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
FONT = "Microsoft JhengHei UI"

def enable_high_dpi():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try: ctypes.windll.user32.SetProcessDPIAware()
        except Exception: pass

class FileRenamerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION}")
        try: self.iconbitmap(str(resource_path("FileRenamer.ico")))
        except Exception: pass
        self.geometry("1100x800"); self.minsize(900,680)
        ctk.set_appearance_mode("System"); ctk.set_default_color_theme("blue")
        self.folder_path=tk.StringVar(); self.prefix=tk.StringVar(value="File"); self.separator=tk.StringVar(value="_")
        self.start_number=tk.StringVar(value="1"); self.digits=tk.StringVar(value="3")
        self.sort_method=tk.StringVar(value="檔案名稱"); self.sort_direction=tk.StringVar(value="升冪")
        self.filter_mode=tk.StringVar(value="所有檔案"); self.custom_extensions=tk.StringVar(value=".jpg, .jpeg, .png")
        self.status_text=tk.StringVar(value="請先選擇資料夾"); self.rename_list=[]; self._preview_job=None
        self.grid_columnconfigure(0,weight=1); self.grid_rowconfigure(4,weight=1)
        self.create_ui(); self.bind_live_preview(); self.update_filter_state(); self.update_undo_button(); self.after(50,self.apply_tree_style)

    def create_ui(self):
        header=ctk.CTkFrame(self,fg_color="transparent"); header.grid(row=0,column=0,sticky="ew",padx=28,pady=(22,14)); header.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(header,text=APP_NAME,font=(FONT,25,"bold")).grid(row=0,column=0,sticky="w")
        ctk.CTkLabel(header,text="快速、安全地批次整理檔案名稱",font=(FONT,13),text_color=("#667085","#98A2B3")).grid(row=1,column=0,sticky="w",pady=(2,0))
        self.theme_switch=ctk.CTkSwitch(header,text="深色模式",font=(FONT,12),command=self.toggle_theme); self.theme_switch.grid(row=0,column=1,rowspan=2,padx=(10,18))
        ctk.CTkLabel(header,text=f"v{APP_VERSION}",font=(FONT,13),text_color=("#667085","#98A2B3")).grid(row=0,column=2,rowspan=2)
        folder=ctk.CTkFrame(self,corner_radius=14); folder.grid(row=1,column=0,sticky="ew",padx=28,pady=(0,12)); folder.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(folder,text="選擇資料夾",font=(FONT,15,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",padx=18,pady=(15,8))
        ctk.CTkEntry(folder,textvariable=self.folder_path,height=38,font=(FONT,13),corner_radius=8).grid(row=1,column=0,sticky="ew",padx=(18,10),pady=(0,16))
        ctk.CTkButton(folder,text="瀏覽…",width=110,height=38,font=(FONT,13),command=self.select_folder).grid(row=1,column=1,padx=(0,18),pady=(0,16))
        options=ctk.CTkFrame(self,fg_color="transparent"); options.grid(row=2,column=0,sticky="ew",padx=28,pady=(0,12)); options.grid_columnconfigure((0,1),weight=1,uniform="opt")
        fc=ctk.CTkFrame(options,corner_radius=14); fc.grid(row=0,column=0,sticky="nsew",padx=(0,6)); fc.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(fc,text="檔案篩選",font=(FONT,15,"bold")).grid(row=0,column=0,sticky="w",padx=18,pady=(15,9))
        self.filter_segment=ctk.CTkSegmentedButton(fc,values=["所有檔案","僅圖片","指定副檔名"],variable=self.filter_mode,font=(FONT,12),command=lambda _=None:self.update_filter_state()); self.filter_segment.grid(row=1,column=0,sticky="ew",padx=18)
        self.extension_entry=ctk.CTkEntry(fc,textvariable=self.custom_extensions,height=34,font=(FONT,12),corner_radius=8); self.extension_entry.grid(row=2,column=0,sticky="ew",padx=18,pady=(10,16))
        sc=ctk.CTkFrame(options,corner_radius=14); sc.grid(row=0,column=1,sticky="nsew",padx=(6,0)); sc.grid_columnconfigure(1,weight=1)
        ctk.CTkLabel(sc,text="排序",font=(FONT,15,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",padx=18,pady=(15,9))
        ctk.CTkLabel(sc,text="依照",font=(FONT,12)).grid(row=1,column=0,sticky="w",padx=(18,10),pady=5)
        ctk.CTkOptionMenu(sc,variable=self.sort_method,values=["檔案名稱","建立時間","修改時間","檔案大小"],font=(FONT,12),height=32).grid(row=1,column=1,sticky="ew",padx=(0,18),pady=5)
        ctk.CTkLabel(sc,text="順序",font=(FONT,12)).grid(row=2,column=0,sticky="w",padx=(18,10),pady=(5,16))
        ctk.CTkSegmentedButton(sc,variable=self.sort_direction,values=["升冪","降冪"],font=(FONT,12)).grid(row=2,column=1,sticky="ew",padx=(0,18),pady=(5,16))
        naming=ctk.CTkFrame(self,corner_radius=14); naming.grid(row=3,column=0,sticky="ew",padx=28,pady=(0,12)); naming.grid_columnconfigure((0,1,2,3),weight=1,uniform="name")
        ctk.CTkLabel(naming,text="命名規則",font=(FONT,15,"bold")).grid(row=0,column=0,columnspan=4,sticky="w",padx=18,pady=(14,7))
        for col,(label,var) in enumerate([("檔名前綴",self.prefix),("分隔符號",self.separator),("起始編號",self.start_number),("編號位數",self.digits)]):
            ctk.CTkLabel(naming,text=label,font=(FONT,12)).grid(row=1,column=col,sticky="w",padx=(18 if col==0 else 7,7))
            ctk.CTkEntry(naming,textvariable=var,height=34,font=(FONT,12),corner_radius=8).grid(row=2,column=col,sticky="ew",padx=(18 if col==0 else 7,18 if col==3 else 7),pady=(4,15))
        preview=ctk.CTkFrame(self,corner_radius=14); preview.grid(row=4,column=0,sticky="nsew",padx=28,pady=(0,12)); preview.grid_columnconfigure(0,weight=1); preview.grid_rowconfigure(1,weight=1)
        top=ctk.CTkFrame(preview,fg_color="transparent"); top.grid(row=0,column=0,columnspan=2,sticky="ew",padx=16,pady=(12,7)); top.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(top,text="預覽",font=(FONT,15,"bold")).grid(row=0,column=0,sticky="w")
        self.count_label=ctk.CTkLabel(top,text="0 個檔案",font=(FONT,12),text_color=("#667085","#98A2B3")); self.count_label.grid(row=0,column=1,sticky="e")
        self.preview_tree=ttk.Treeview(preview,columns=("old","arrow","new"),show="headings",selectmode="browse")
        self.preview_tree.heading("old",text="原始檔名"); self.preview_tree.heading("arrow",text=""); self.preview_tree.heading("new",text="新檔名")
        self.preview_tree.column("old",width=390,minwidth=160,anchor="w"); self.preview_tree.column("arrow",width=44,minwidth=44,stretch=False,anchor="center"); self.preview_tree.column("new",width=390,minwidth=160,anchor="w")
        yscroll=ctk.CTkScrollbar(preview,orientation="vertical",command=self.preview_tree.yview); self.preview_tree.configure(yscrollcommand=yscroll.set)
        self.preview_tree.grid(row=1,column=0,sticky="nsew",padx=(16,6),pady=(0,14)); yscroll.grid(row=1,column=1,sticky="ns",padx=(0,10),pady=(0,14))
        footer=ctk.CTkFrame(self,fg_color="transparent"); footer.grid(row=5,column=0,sticky="ew",padx=28,pady=(0,20)); footer.grid_columnconfigure(1,weight=1)
        self.undo_button=ctk.CTkButton(footer,text="↶  復原上次操作",width=155,height=40,font=(FONT,12),fg_color="transparent",border_width=1,text_color=("#344054","#D0D5DD"),command=self.undo_rename); self.undo_button.grid(row=0,column=0,sticky="w")
        self.status_label=ctk.CTkLabel(footer,textvariable=self.status_text,font=(FONT,12),text_color=("#667085","#98A2B3"),anchor="w"); self.status_label.grid(row=0,column=1,sticky="ew",padx=16)
        self.rename_button=ctk.CTkButton(footer,text="開始重新命名",width=160,height=42,font=(FONT,13,"bold"),command=self.rename_files); self.rename_button.grid(row=0,column=2,sticky="e")

    def toggle_theme(self):
        ctk.set_appearance_mode("Dark" if self.theme_switch.get() else "Light"); self.after(50,self.apply_tree_style)

    def apply_tree_style(self):
        dark=ctk.get_appearance_mode()=="Dark"; bg="#242424" if dark else "#FFFFFF"; fg="#F2F4F7" if dark else "#101828"; head="#2B2B2B" if dark else "#F2F4F7"
        style=ttk.Style(self)
        try: style.theme_use("clam")
        except Exception: pass
        style.configure("Treeview",background=bg,fieldbackground=bg,foreground=fg,rowheight=30,borderwidth=0,font=(FONT,10)); style.configure("Treeview.Heading",background=head,foreground=fg,relief="flat",font=(FONT,10,"bold")); style.map("Treeview",background=[("selected","#1F6AA5")],foreground=[("selected","#FFFFFF")])

    def bind_live_preview(self):
        for v in [self.folder_path,self.prefix,self.separator,self.start_number,self.digits,self.sort_method,self.sort_direction,self.filter_mode,self.custom_extensions]: v.trace_add("write",self.schedule_preview)
    def schedule_preview(self,*_):
        if self._preview_job is not None: self.after_cancel(self._preview_job)
        self._preview_job=self.after(140,self.preview)
    def update_filter_state(self): self.extension_entry.configure(state="normal" if self.filter_mode.get()=="指定副檔名" else "disabled"); self.schedule_preview()
    def update_undo_button(self): self.undo_button.configure(state="normal" if HISTORY_FILE.exists() else "disabled")
    def select_folder(self):
        folder=filedialog.askdirectory()
        if folder: self.folder_path.set(folder)
    @staticmethod
    def natural_sort_key(path): return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)",path.name)]
    def get_files(self):
        text=self.folder_path.get().strip()
        if not text:return []
        folder=Path(text)
        if not folder.is_dir():return []
        protected={HISTORY_FILE.resolve()}
        if not getattr(sys,"frozen",False):protected.add(Path(__file__).resolve())
        files=[f for f in folder.iterdir() if f.is_file() and f.resolve() not in protected]
        mode=self.filter_mode.get()
        if mode=="僅圖片": files=[f for f in files if f.suffix.lower() in IMAGE_EXTENSIONS]
        elif mode=="指定副檔名":
            exts=set()
            for ext in self.custom_extensions.get().replace(";",",").split(","):
                ext=ext.strip().lower()
                if ext:exts.add(ext if ext.startswith(".") else "."+ext)
            files=[f for f in files if f.suffix.lower() in exts]
        reverse=self.sort_direction.get()=="降冪"; method=self.sort_method.get(); key=self.natural_sort_key
        if method=="建立時間":key=lambda x:x.stat().st_ctime
        elif method=="修改時間":key=lambda x:x.stat().st_mtime
        elif method=="檔案大小":key=lambda x:x.stat().st_size
        files.sort(key=key,reverse=reverse); return files
    def clear_preview(self): self.preview_tree.delete(*self.preview_tree.get_children())
    def preview(self):
        self._preview_job=None; self.clear_preview(); self.rename_list.clear(); files=self.get_files()
        if not files:
            self.count_label.configure(text="0 個檔案"); self.status_text.set("沒有符合條件的檔案" if self.folder_path.get().strip() else "請先選擇資料夾"); self.rename_button.configure(state="disabled"); return
        try:
            start=int(self.start_number.get()); digits=int(self.digits.get())
            if start<0 or not 1<=digits<=10:raise ValueError
        except ValueError:
            self.count_label.configure(text="0 個檔案"); self.status_text.set("起始編號或編號位數格式錯誤"); self.rename_button.configure(state="disabled"); return
        prefix=self.prefix.get().strip(); sep=self.separator.get()
        for i,old in enumerate(files):
            number=f"{start+i:0{digits}d}"; stem=f"{prefix}{sep}{number}" if prefix else number; new=old.parent/f"{stem}{old.suffix}"
            self.rename_list.append((old,new)); self.preview_tree.insert("","end",values=(old.name,"→",new.name if old!=new else f"{new.name}  （不變）"))
        self.count_label.configure(text=f"{len(self.rename_list)} 個檔案"); pairs=[(a,b) for a,b in self.rename_list if a!=b]; safe,msg=self.check_conflicts(pairs)
        if not pairs:self.status_text.set("✓ 目前名稱已符合設定，不需要變更"); self.rename_button.configure(state="disabled")
        elif safe:self.status_text.set(f"✓ {len(pairs)} 個檔案準備重新命名"); self.rename_button.configure(state="normal")
        else:self.status_text.set("⚠ "+msg.replace("\n"," ")); self.rename_button.configure(state="disabled")
    @staticmethod
    def create_temp_path(folder,prefix,index):
        counter=0
        while True:
            p=folder/f".{prefix}_{index}_{counter}.tmp"
            if not p.exists():return p
            counter+=1
    def check_conflicts(self,pairs):
        sources={str(old.resolve()).casefold() for old,_ in pairs}; targets=set()
        for _,new in pairs:
            key=str(new.resolve()).casefold()
            if key in targets:return False,f"有多個檔案會變成 {new.name}"
            targets.add(key)
            if new.exists() and key not in sources:return False,f"目標檔名已存在：{new.name}"
        return True,""
    @staticmethod
    def write_history(history):
        with open(HISTORY_FILE,"w",encoding="utf-8") as f:json.dump(history,f,ensure_ascii=False,indent=4)
    def rename_files(self):
        self.preview(); pairs=[(a,b) for a,b in self.rename_list if a!=b]
        if not pairs:messagebox.showinfo("沒有變更","目前沒有需要重新命名的檔案。"); return
        safe,msg=self.check_conflicts(pairs)
        if not safe:messagebox.showerror("檔名衝突",msg); return
        if not messagebox.askyesno("確認重新命名",f"確定要重新命名 {len(pairs)} 個檔案嗎？"):return
        staged=[]
        try:
            for i,(old,new) in enumerate(pairs):
                temp=self.create_temp_path(old.parent,"rename_temp",i); old.rename(temp); staged.append({"old":old,"temp":temp,"new":new,"finished":False})
            for item in staged:item["temp"].rename(item["new"]); item["finished"]=True
            self.write_history([{"old":str(x["old"]),"new":str(x["new"])} for x in staged]); self.update_undo_button(); messagebox.showinfo("完成","重新命名完成！\n如果結果不滿意，可以使用「復原上次操作」。"); self.preview()
        except Exception as error:
            failed=False
            for item in reversed(staged):
                try:
                    if item["finished"] and item["new"].exists():item["new"].rename(item["old"])
                    elif item["temp"].exists():item["temp"].rename(item["old"])
                except Exception:failed=True
            messagebox.showerror("嚴重錯誤" if failed else "重新命名失敗",("部分檔案無法自動恢復，請先不要繼續操作該資料夾。\n\n" if failed else "發生錯誤，已嘗試恢復原始檔名。\n\n")+str(error)); self.preview()
    def undo_rename(self):
        if not HISTORY_FILE.exists():self.update_undo_button(); messagebox.showinfo("沒有紀錄","目前沒有可以復原的重新命名紀錄。"); return
        try:
            with open(HISTORY_FILE,"r",encoding="utf-8") as f:history=json.load(f)
        except Exception as e:messagebox.showerror("錯誤",f"無法讀取復原紀錄：\n{e}"); return
        pairs=[(Path(x["new"]),Path(x["old"])) for x in history]; currents={str(a.resolve()).casefold() for a,_ in pairs}
        for current,original in pairs:
            if not current.exists():messagebox.showerror("無法復原",f"找不到重新命名後的檔案：\n{current}"); return
            if original.exists() and str(original.resolve()).casefold() not in currents:messagebox.showerror("無法復原",f"原始檔名目前已被其他檔案占用：\n{original.name}"); return
        if not messagebox.askyesno("確認復原",f"確定要復原上一次的 {len(history)} 個檔案嗎？"):return
        staged=[]
        try:
            for i,(current,original) in enumerate(pairs):
                temp=self.create_temp_path(current.parent,"undo_temp",i); current.rename(temp); staged.append({"current":current,"original":original,"temp":temp,"finished":False})
            for item in staged:item["temp"].rename(item["original"]); item["finished"]=True
            HISTORY_FILE.unlink(); self.update_undo_button(); messagebox.showinfo("完成","已成功復原上一次重新命名！"); self.preview()
        except Exception as error:
            failed=False
            for item in reversed(staged):
                try:
                    if item["finished"] and item["original"].exists():item["original"].rename(item["current"])
                    elif item["temp"].exists():item["temp"].rename(item["current"])
                except Exception:failed=True
            messagebox.showerror("嚴重錯誤" if failed else "復原失敗",("部分檔案無法回復到 Undo 前狀態。\n\n" if failed else "Undo 發生錯誤，已嘗試回復到 Undo 前狀態。\n\n")+str(error)); self.preview()

if __name__=="__main__":
    enable_high_dpi(); FileRenamerApp().mainloop()
