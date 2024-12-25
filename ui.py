from json import dump
from structs.field import Field
from structs.entity import Entity, EntityScript
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
        # Row 0: Header
        row0 = ttk.Frame(parent)
        row0.pack(fill="x", padx=5, pady=5)
        ttk.Label(row0, text="Scale:").pack(side=tk.LEFT, padx=5)
        self.scale_var = tk.StringVar(value="")
        tk.Entry(row0, textvariable=self.scale_var, width=15).pack(side=tk.LEFT)
        ttk.Label(row0, text="Creator:").pack(side=tk.LEFT, padx=5)
        self.creator_var = tk.StringVar(value="")
        tk.Entry(row0, textvariable=self.creator_var, width=30).pack(side=tk.LEFT)
        ttk.Label(row0, text="Name:").pack(side=tk.LEFT, padx=5)
        self.name_var = tk.StringVar(value="")
        tk.Entry(row0, textvariable=self.name_var, width=30).pack(side=tk.LEFT)
        # Row 1: Dialogs
        row1 = ttk.Frame(parent)
        row1.pack(fill="x", padx=5, pady=5)
        dialogs_frame = ttk.LabelFrame(row1, text="Dialogs")
        dialogs_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        scrollDialog = tk.Scrollbar(dialogs_frame, orient=tk.VERTICAL)
        scrollDialog.pack(side=tk.RIGHT, fill=tk.Y)
        self.dialogs_list = tk.Listbox(dialogs_frame, width=20, height=8)
        self.dialogs_list.pack(side=tk.LEFT,fill=tk.Y, expand=True)
        scrollDialog.config(command=self.dialogs_list.yview)
        self.dialogs_list.config(yscrollcommand=scrollDialog.set)
        self.dialogs_list.bind("<<ListboxSelect>>", self.on_dialog_selected)
        self.dialog_text = tk.Text(dialogs_frame, width=100, height= 8)
        self.dialog_text.pack(side=tk.RIGHT,fill=tk.Y, expand=True)
        # Row 2: Scripts
        row2 = ttk.Frame(parent)
        row2.pack(fill=tk.BOTH, padx=5, pady=5)
        entities_frame = ttk.LabelFrame(row2, text="Entities")
        entities_frame.pack(side=tk.LEFT, fill=tk.Y, expand=True, padx=5)
        scrollEntity = tk.Scrollbar(entities_frame, orient=tk.VERTICAL)
        scrollEntity.pack(side=tk.RIGHT, fill=tk.Y)
        self.entities_list = tk.Listbox(entities_frame, width=20, height=5)
        self.entities_list.pack(fill=tk.Y, expand=True)
        scrollEntity.config(command=self.entities_list.yview)
        self.entities_list.config(yscrollcommand=scrollEntity.set)
        self.entities_list.bind("<<ListboxSelect>>", self.on_entity_selected)
        entity_script_frame = ttk.LabelFrame(row2, text="Entity Scripts")
        entity_script_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.entity_scripts_list = tk.Listbox(entity_script_frame, height=8, width=5)
        self.entity_scripts_list.pack(side=tk.LEFT,fill=tk.BOTH, expand=True, padx=5)
        self.entity_scripts_list.bind("<<ListboxSelect>>", self.on_entity_script_selected)
        self.script_text = tk.Text(entity_script_frame, width=50, height= 8)
        self.script_text.pack(side=tk.RIGHT,fill=tk.BOTH, expand=True)

    def openfile(self):
        filepath = filedialog.askopenfilename(title="FF7 Field DAT", filetypes=[("DAT Files", "*.DAT")])
        if not filepath:
            return
        self.field = Field(filepath)
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
            self.entity_scripts_list.insert(tk.END, str(script))
        self.script_text.delete(1.0, tk.END)

    def on_entity_script_selected(self, event):
        selection = event.widget.curselection()
        if not selection:
            self.entity_script = None
            return
        index = selection[0]
        self.entity_script = self.entity.scripts[index]
        self.script_text.delete(1.0, tk.END)
        for opcode in self.entity_script.opcodes:
            self.script_text.insert(tk.END, str(opcode) + "\n")


if __name__ == '__main__':
    app = FieldForm()
    app.mainloop()