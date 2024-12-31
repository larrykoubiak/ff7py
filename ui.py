from json import dump
from constructs.akao import AKAO, AKAOScript
from constructs.field import Field, Entity, EntityScript, Walkmesh, Camera, Tilemap
from constructs.mim import MIM
from pyopengltk import OpenGLFrame
from OpenGL.GL import *
from OpenGL.GLU import *
from tkinter import ttk, filedialog
from PIL import ImageTk, Image
import math
import tkinter as tk

class WalkmeshFrame(OpenGLFrame):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.walkmesh: Walkmesh = None
        self.camera: Camera = None

    def set_walkmesh_camera(self, walkmesh, camera):
        self.walkmesh = walkmesh
        self.camera = camera

    def initgl(self):
        glClearColor(0.2, 0.2, 0.2, 1.0)
        glEnable(GL_DEPTH_TEST)

    def redraw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(
            70,
            self.width / float(self.height), 
            0.001, 
            1000.0
        )

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        if self.walkmesh:
            gluLookAt(
                self.camera.tx, self.camera.ty, self.camera.tz,
                self.camera.tx + self.camera.axis_z.x, self.camera.ty + self.camera.axis_z.y, self.camera.tz + self.camera.axis_z.z,
                self.camera.axis_y.x, self.camera.axis_y.y, self.camera.axis_y.z
            )
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glColor3f(1.0, 1.0, 1.0)  # White lines
            glBegin(GL_TRIANGLES)
            for t in self.walkmesh.triangles:
                for v in t.vertices:
                    glVertex3f(v.x / 4096, v.y / 4096, v.z / 4096)
            glEnd()
            # Restore to fill mode if you plan to draw something else
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

class FieldForm(tk.Tk):
    def __init__(self, screenName = None, baseName = None, className = "Tk", useTk = True, sync = False, use = None):
        super().__init__(screenName, baseName, className, useTk, sync, use)
        self.field: Field = None
        self.entity: Entity = None
        self.entity_script: EntityScript = None
        self.akao: AKAO = None
        self.akao_script: AKAOScript = None
        self.mim: MIM = None
        self.mim_image: ImageTk.PhotoImage = None
        self.tilemap_image: ImageTk.PhotoImage = None
        self.title("FF7 Field Editor")
        self.geometry("1024x534")
        self.buildMenu() # Config Menu
        self.buildTabs() # Tab Controls

    def buildMenu(self):
        menubar = tk.Menu(self)
        fileMenu = tk.Menu(menubar)
        fileMenu.add_command(label="Open", command=self.openfile)
        fileMenu.add_command(label="Save", command=self.savefile)
        menubar.add_cascade(label="File", menu=fileMenu)
        self.config(menu=menubar)

    def buildTabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        # Script
        script_tab = ttk.Frame(self.notebook)
        self.notebook.add(script_tab, text="Script")
        self.buildScript(script_tab)
        # Mesh
        mesh_tab = ttk.Frame(self.notebook)
        self.notebook.add(mesh_tab, text="Mesh")
        self.buildMesh(mesh_tab)
        # MIM
        mim_tab = ttk.Frame(self.notebook)
        self.notebook.add(mim_tab, text="MIM")
        self.buildMIM(mim_tab)
        #Tilemap
        tilemap_tab = ttk.Frame(self.notebook)
        self.notebook.add(tilemap_tab, text="Tilemap")
        self.buildTilemap(tilemap_tab)

    def buildScript(self, parent):
        """
        Build the script UI using grid geometry. We remove hard-coded widths/heights and rely on grid weights to achieve proportional resizing.
        """
        parent.rowconfigure(0, weight=0)
        parent.rowconfigure(1, weight=1)
        parent.rowconfigure(2, weight=1)
        parent.rowconfigure(3, weight=1)
        parent.columnconfigure(0, weight=1)
        # ──────────────────────────────────────────────────────────────────────
        # Row 0: Header (Scale, Creator, Name)
        # ──────────────────────────────────────────────────────────────────────
        row0 = ttk.Frame(parent)
        row0.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        for col in range(6):
            row0.columnconfigure(col, weight=1 if col % 2 == 1 else 0)
        # Scale
        ttk.Label(row0, text="Scale:").grid(row=0, column=0, sticky="w", padx=5)
        self.scale_var = tk.StringVar(value="")
        tk.Entry(row0, textvariable=self.scale_var).grid(row=0, column=1, sticky="ew")
        # Creator
        ttk.Label(row0, text="Creator:").grid(row=0, column=2, sticky="w", padx=5)
        self.creator_var = tk.StringVar(value="")
        tk.Entry(row0, textvariable=self.creator_var).grid(row=0, column=3, sticky="ew")
        # Name
        ttk.Label(row0, text="Name:").grid(row=0, column=4, sticky="w", padx=5)
        self.name_var = tk.StringVar(value="")
        tk.Entry(row0, textvariable=self.name_var).grid(row=0, column=5, sticky="ew")
        # ──────────────────────────────────────────────────────────────────────
        # Row 1: Dialogs
        # ──────────────────────────────────────────────────────────────────────
        row1 = ttk.Frame(parent)
        row1.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        row1.rowconfigure(0, weight=1)
        row1.columnconfigure(0, weight=1)
        dialogs_frame = ttk.LabelFrame(row1, text="Dialogs")
        dialogs_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        dialogs_frame.rowconfigure(0, weight=1)
        dialogs_frame.columnconfigure(0, weight=1)  # Listbox
        dialogs_frame.columnconfigure(1, weight=0)  # Scrollbar
        dialogs_frame.columnconfigure(2, weight=2)  # Text gets more space
        # Dialogs List + Scrollbar
        scrollDialog = tk.Scrollbar(dialogs_frame, orient=tk.VERTICAL)
        scrollDialog.grid(row=0, column=1, sticky="ns")
        self.dialogs_list = tk.Listbox(dialogs_frame, yscrollcommand=scrollDialog.set)
        self.dialogs_list.grid(row=0, column=0, sticky="nsew")
        scrollDialog.config(command=self.dialogs_list.yview)
        self.dialogs_list.bind("<<ListboxSelect>>", self.on_dialog_selected)
        # Dialog Text
        self.dialog_text = tk.Text(dialogs_frame)
        self.dialog_text.grid(row=0, column=2, sticky="nsew")
        # ──────────────────────────────────────────────────────────────────────
        # Row 2: Scripts / Entities
        # ──────────────────────────────────────────────────────────────────────
        row2 = ttk.Frame(parent)
        row2.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        row2.rowconfigure(0, weight=1)
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=2)
        entities_frame = ttk.LabelFrame(row2, text="Entities")
        entities_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        entities_frame.rowconfigure(0, weight=1)
        entities_frame.columnconfigure(0, weight=1)  # Listbox
        entities_frame.columnconfigure(1, weight=0)  # Scrollbar
        scrollEntity = tk.Scrollbar(entities_frame, orient=tk.VERTICAL)
        scrollEntity.grid(row=0, column=1, sticky="ns")
        self.entities_list = tk.Listbox(
            entities_frame, yscrollcommand=scrollEntity.set
        )
        self.entities_list.grid(row=0, column=0, sticky="nsew")
        scrollEntity.config(command=self.entities_list.yview)
        self.entities_list.bind("<<ListboxSelect>>", self.on_entity_selected)
        entity_script_frame = ttk.LabelFrame(row2, text="Entity Scripts")
        entity_script_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        entity_script_frame.rowconfigure(0, weight=1)
        entity_script_frame.columnconfigure(0, weight=1)
        entity_script_frame.columnconfigure(1, weight=2)
        self.entity_scripts_list = tk.Listbox(entity_script_frame)
        self.entity_scripts_list.grid(row=0, column=0, sticky="nsew", padx=5)
        self.entity_scripts_list.bind("<<ListboxSelect>>", self.on_entity_script_selected)
        self.entity_script_text = tk.Text(entity_script_frame)
        self.entity_script_text.grid(row=0, column=1, sticky="nsew")
        # ──────────────────────────────────────────────────────────────────────
        # Row 3: Scripts / AKAOs
        # ──────────────────────────────────────────────────────────────────────
        # ──────────────────────────────────────────────────────────────────────
        # Row 3: Scripts / AKAOs
        # ──────────────────────────────────────────────────────────────────────
        row3 = ttk.Frame(parent)
        row3.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        row3.rowconfigure(0, weight=1)
        row3.columnconfigure(0, weight=1)
        row3.columnconfigure(1, weight=2)
        AKAOs_frame = ttk.LabelFrame(row3, text="AKAOs")
        AKAOs_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        AKAOs_frame.rowconfigure(0, weight=1)
        AKAOs_frame.columnconfigure(0, weight=1)  # Listbox
        AKAOs_frame.columnconfigure(1, weight=0)  # Scrollbar
        scrollakao = tk.Scrollbar(AKAOs_frame, orient=tk.VERTICAL)
        scrollakao.grid(row=0, column=1, sticky="ns")
        self.akaos_list = tk.Listbox(
            AKAOs_frame, yscrollcommand=scrollakao.set
        )
        self.akaos_list.grid(row=0, column=0, sticky="nsew")
        scrollakao.config(command=self.akaos_list.yview)
        self.akaos_list.bind("<<ListboxSelect>>", self.on_akao_selected)
        akao_script_frame = ttk.LabelFrame(row3, text="AKAO Scripts")
        akao_script_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        akao_script_frame.rowconfigure(0, weight=1)
        akao_script_frame.columnconfigure(0, weight=1)
        akao_script_frame.columnconfigure(1, weight=2)
        self.akao_scripts_list = tk.Listbox(akao_script_frame)
        self.akao_scripts_list.grid(row=0, column=0, sticky="nsew", padx=5)
        self.akao_scripts_list.bind("<<ListboxSelect>>", self.on_akao_script_selected)
        self.akao_script_text = tk.Text(akao_script_frame)
        self.akao_script_text.grid(row=0, column=1, sticky="nsew")

    def buildMIM(self, parent):
        self.mim_frame = ttk.Label(parent, image=self.mim_image)
        self.mim_frame.pack(fill=tk.BOTH, expand=True)
        self.mim_frame.bind("<Configure>", self.on_label_resize)

    def buildMesh(self, parent):
        self.ogl_frame = WalkmeshFrame(parent, width=1024, height=512)
        self.ogl_frame.pack(fill=tk.BOTH, expand=True)
        self.ogl_frame.animate = 0

    def buildTilemap(self, parent):
        self.tilemap_frame = ttk.Label(parent, image=self.mim_image)
        self.tilemap_frame.pack(fill=tk.BOTH, expand=True)
        self.tilemap_frame.bind("<Configure>", self.on_label_resize)

    def openfile(self):
        filepath = filedialog.askopenfilename(title="FF7 Field DAT", filetypes=[("DAT Files", "*.DAT")])
        if not filepath:
            return
        self.field = Field.from_file(filepath)
        mimfilepath = filepath.replace(".DAT",".MIM")
        self.mim = MIM.from_file(mimfilepath)
        self.refresh()

    def savefile(self):
        with open("output/test.json", "w", encoding="utf-8") as f:
            dic = self.field.dump()
            dump(dic, f, indent=2,ensure_ascii=False)

    def refresh(self):
        self.scale_var.set(str(self.field.script.scale))
        self.creator_var.set(self.field.script.creator)
        self.name_var.set(self.field.script.name)
        self.dialogs_list.delete(0, tk.END)
        for index in range(len(self.field.script.dialogs)):
            self.dialogs_list.insert(tk.END, f"Dialog {index}")
        self.entities_list.delete(0, tk.END)
        for ent in self.field.script.entities:
            self.entities_list.insert(tk.END, ent.name)
        self.akaos_list.delete(0, tk.END)
        for akao in self.field.script.akaos:
            self.akaos_list.insert(tk.END, str(akao.id))
        original_image = self.mim.get_image_data(0)
        self.mim_image = ImageTk.PhotoImage(original_image)
        self.resize_mim(self.winfo_width(), self.winfo_height()-32)
        self.ogl_frame.set_walkmesh_camera(self.field.walkmesh, self.field.camera)
        self.ogl_frame.animate = 1
        original_image = self.field.tilemap.get_image_data(self.mim)
        self.tilemap_image = ImageTk.PhotoImage(original_image)
        self.resize_tilemap(self.winfo_width(), self.winfo_height()-32)

    def on_dialog_selected(self, event):
        selection = event.widget.curselection()
        if not selection:
            return
        index = selection[0]
        dialog = self.field.script.dialogs[index]
        mapping = [('{SPACE}',' '),('{Choice}','• '),('{Tab}','  '),('{EOL}','\n'),('{New Scr}','\n\n---{New Screen}---\n\n'),('{END}','')]
        for k, v in mapping:
            dialog = dialog.replace(k, v)
        self.dialog_text.delete(1.0, tk.END)
        self.dialog_text.insert(tk.END, dialog)

    def on_entity_selected(self, event):
        selection = event.widget.curselection()
        if not selection:
            return
        index = selection[0]
        self.entity = self.field.script.entities[index]
        self.entity_scripts_list.delete(0, tk.END)
        for script in self.entity.scripts:
            self.entity_scripts_list.insert(tk.END, f"Address {script.address}")
        self.entity_script_text.delete(1.0, tk.END)

    def on_entity_script_selected(self, event):
        selection = event.widget.curselection()
        if not selection:
            self.entity_script = None
            return
        index = selection[0]
        self.entity_script = self.entity.scripts[index]
        self.entity_script_text.delete(1.0, tk.END)
        for opcode in self.entity_script.instructions:
            self.entity_script_text.insert(tk.END, str(opcode) + "\n")

    def on_akao_selected(self, event):
        selection = event.widget.curselection()
        if not selection:
            return
        index = selection[0]
        self.akao = self.field.script.akaos[index]
        self.akao_scripts_list.delete(0, tk.END)
        for script in self.akao.scripts:
            self.akao_scripts_list.insert(tk.END, f"Address {script.address}")
        self.akao_script_text.delete(1.0, tk.END)

    def on_akao_script_selected(self, event):
        selection = event.widget.curselection()
        if not selection:
            self.akao_script = None
            return
        index = selection[0]
        self.akao_script = self.akao.scripts[index]
        self.akao_script_text.delete(1.0, tk.END)
        for opcode in self.akao_script.instructions:
            self.akao_script_text.insert(tk.END, str(opcode) + "\n")

    def on_label_resize(self, event):
        max_width = event.width
        max_height = event.height
        if self.mim is not None:
            self.resize_mim(max_width, max_height)

    def resize_mim(self, max_width, max_height):
        original_image = self.mim.get_image_data(0)
        ow, oh = original_image.size
        width_ratio = max_width / ow
        height_ratio = max_height / oh
        scale_factor = min(width_ratio, height_ratio)
        new_width = int(ow * scale_factor)
        new_height = int(oh * scale_factor)
        new_image = original_image.resize((new_width, new_height),resample=Image.Resampling.LANCZOS)
        self.mim_image = ImageTk.PhotoImage(new_image)
        self.mim_frame.config(image=self.mim_image)

    def resize_tilemap(self, max_width, max_height):
        original_image = self.field.tilemap.get_image_data(self.mim)
        ow, oh = original_image.size
        width_ratio = max_width / ow
        height_ratio = max_height / oh
        scale_factor = min(width_ratio, height_ratio)
        new_width = int(ow * scale_factor)
        new_height = int(oh * scale_factor)
        new_image = original_image.resize((new_width, new_height),resample=Image.Resampling.LANCZOS)
        self.tilemap_image = ImageTk.PhotoImage(new_image)
        self.tilemap_frame.config(image=self.tilemap_image)

if __name__ == '__main__':
    app = FieldForm()
    app.mainloop()