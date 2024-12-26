from json import dump
from field import Field, Entity, EntityScript
import tkinter as tk
from tkinter import ttk, filedialog

class FieldForm(tk.Tk):
    def __init__(self, screenName = None, baseName = None, className = "Tk", useTk = True, sync = False, use = None):
        super().__init__(screenName, baseName, className, useTk, sync, use)
        self.field: Field = None
        self.entity: Entity = None
        self.entity_script: EntityScript = None
        self.title("FF7 Field Editor")
        self.geometry("976x534")
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
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)
        # Script
        script_tab = ttk.Frame(notebook)
        notebook.add(script_tab, text="Script")
        self.buildScript(script_tab)
        # Mesh
        mesh_tab = ttk.Frame(notebook)
        notebook.add(mesh_tab, text="Mesh")
        #Tilemap
        tilemap_tab = ttk.Frame(notebook)
        notebook.add(tilemap_tab, text="Tilemap")

    def buildScript(self, parent):
        """
        Build the script UI using grid geometry. We remove hard-coded widths/heights and rely on grid weights to achieve proportional resizing.
        """
        parent.rowconfigure(0, weight=0)
        parent.rowconfigure(1, weight=1)
        parent.rowconfigure(2, weight=1)
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
        self.script_text = tk.Text(entity_script_frame)
        self.script_text.grid(row=0, column=1, sticky="nsew")

    def openfile(self):
        filepath = filedialog.askopenfilename(title="FF7 Field DAT", filetypes=[("DAT Files", "*.DAT")])
        if not filepath:
            return
        self.field = Field.from_file(filepath)
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
        self.script_text.delete(1.0, tk.END)

    def on_entity_script_selected(self, event):
        selection = event.widget.curselection()
        if not selection:
            self.entity_script = None
            return
        index = selection[0]
        self.entity_script = self.entity.scripts[index]
        self.script_text.delete(1.0, tk.END)
        for opcode in self.entity_script.instructions:
            self.script_text.insert(tk.END, str(opcode) + "\n")


if __name__ == '__main__':
    app = FieldForm()
    app.mainloop()