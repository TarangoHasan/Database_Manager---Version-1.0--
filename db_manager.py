import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, scrolledtext
import sqlite3
import os
import csv
import shutil

class DataManager:
    def __init__(self, root):
        self.root = root
        self.root.title("SQLite Database Manager")
        self.current_db = None
        self.current_table = None
        self.sidebar = None           # For table context sidebar
        self.data_context_menu = None # Context menu for data rows

        # Create menu bar
        self.menu_bar = tk.Menu(root)
        
        # File Menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New Database", command=self.new_database)
        self.file_menu.add_command(label="Open Database", command=self.open_database)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Run Query", command=self.run_query_window)
        self.file_menu.add_command(label="Backup Database", command=self.backup_database)
        self.file_menu.add_command(label="Import CSV", command=self.import_csv_to_table)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=root.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        # Tutorial Menu
        self.tutorial_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.tutorial_menu.add_command(label="Show Tutorial", command=self.show_tutorial)
        self.menu_bar.add_cascade(label="Tutorial", menu=self.tutorial_menu)
        
        self.root.config(menu=self.menu_bar)

        # Main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Database Info
        self.db_info_frame = ttk.LabelFrame(self.main_frame, text="Database Information")
        self.db_info_frame.pack(fill=tk.X, pady=5)
        self.db_path_label = ttk.Label(self.db_info_frame, text="No database selected")
        self.db_path_label.pack(side=tk.LEFT, padx=5)

        # Left Frame for Tables
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Tables List
        self.tables_frame = ttk.LabelFrame(self.left_frame, text="Tables")
        self.tables_frame.pack(fill=tk.BOTH, expand=True)
        self.tables_tree = ttk.Treeview(self.tables_frame, height=15)
        self.tables_tree.pack(fill=tk.BOTH, expand=True)
        # Bind left-click for loading data and right-click for table sidebar
        self.tables_tree.bind("<<TreeviewSelect>>", self.load_table_data)
        self.tables_tree.bind("<Button-3>", self.show_table_sidebar)

        # Table Controls (Create, Delete, and Refresh)
        self.table_controls = ttk.Frame(self.left_frame)
        self.table_controls.pack(pady=5)
        self.create_table_btn = ttk.Button(self.table_controls, text="Create Table", command=self.create_table_dialog)
        self.create_table_btn.pack(side=tk.LEFT, padx=2)
        self.delete_table_btn = ttk.Button(self.table_controls, text="Delete Table", command=self.delete_table)
        self.delete_table_btn.pack(side=tk.LEFT, padx=2)
        self.refresh_tables_btn = ttk.Button(self.table_controls, text="Refresh Tables", command=self.load_tables)
        self.refresh_tables_btn.pack(side=tk.LEFT, padx=2)

        # Right Frame for Data Display
        self.data_frame = ttk.LabelFrame(self.main_frame, text="Table Data")
        self.data_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Data Search Field
        self.search_var = tk.StringVar()
        search_frame = ttk.Frame(self.data_frame)
        search_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_data)

        # Data Treeview
        self.data_tree = ttk.Treeview(self.data_frame)
        self.data_tree.pack(fill=tk.BOTH, expand=True)
        # Bind right-click for data context menu (older Toplevel menu style)
        self.data_tree.bind("<Button-3>", self.show_data_context_menu)

        # Data Controls (Add, Edit, Delete, Refresh, Export buttons)
        self.data_controls = ttk.Frame(self.data_frame)
        self.data_controls.pack(pady=5)
        self.add_data_btn = ttk.Button(self.data_controls, text="Add Data", command=self.add_data_dialog)
        self.add_data_btn.pack(side=tk.LEFT, padx=2)
        self.edit_data_btn = ttk.Button(self.data_controls, text="Edit Data", command=self.edit_data_dialog)
        self.edit_data_btn.pack(side=tk.LEFT, padx=2)
        self.delete_data_btn = ttk.Button(self.data_controls, text="Delete Data", command=self.delete_data)
        self.delete_data_btn.pack(side=tk.LEFT, padx=2)
        self.refresh_data_btn = ttk.Button(self.data_controls, text="Refresh Data", command=lambda: self.load_table_data(None))
        self.refresh_data_btn.pack(side=tk.LEFT, padx=2)
        self.export_data_btn = ttk.Button(self.data_controls, text="Export Table to CSV", command=self.export_table_csv)
        self.export_data_btn.pack(side=tk.LEFT, padx=2)

        # Additional friendly feature: Status Bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        self.status_bar.pack(fill=tk.X, padx=2, pady=(2,0))

    # --------------------- Status Helper --------------------- #
    def set_status(self, message):
        self.status_var.set(message)
        self.root.after(3000, lambda: self.status_var.set("Ready"))

    # --------------------- Database & Table Functions --------------------- #
    def new_database(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite Database", "*.db")])
        if file_path:
            try:
                open(file_path, 'w').close()
                self.current_db = file_path
                self.db_path_label.config(text=file_path)
                self.load_tables()
                messagebox.showinfo("Success", "New database created successfully")
                self.set_status("New database created successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create database: {str(e)}")

    def open_database(self):
        file_path = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db")])
        if file_path:
            self.current_db = file_path
            self.db_path_label.config(text=file_path)
            self.load_tables()
            self.set_status("Database opened")

    def backup_database(self):
        if not self.current_db:
            messagebox.showwarning("Warning", "No database to backup")
            return
        backup_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite Database", "*.db")],
                                                   title="Backup Database As")
        if backup_path:
            try:
                shutil.copy(self.current_db, backup_path)
                messagebox.showinfo("Success", f"Database backed up to {backup_path}")
                self.set_status("Database backed up")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to backup database: {str(e)}")

    def import_csv_to_table(self):
        if not self.current_table:
            messagebox.showwarning("Warning", "Please select a table to import data into")
            return
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")],
                                               title="Select CSV File")
        if file_path:
            try:
                conn = sqlite3.connect(self.current_db)
                cursor = conn.cursor()
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    headers = next(reader)  # assume first row is header
                    for row in reader:
                        placeholders = ", ".join(["?"] * len(row))
                        query = f"INSERT INTO {self.current_table} VALUES ({placeholders})"
                        cursor.execute(query, row)
                conn.commit()
                conn.close()
                self.load_table_data(None)
                messagebox.showinfo("Success", f"Data imported from {file_path}")
                self.set_status("CSV data imported")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import CSV: {str(e)}")

    def load_tables(self):
        self.tables_tree.delete(*self.tables_tree.get_children())
        if self.current_db:
            try:
                conn = sqlite3.connect(self.current_db)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                for table in tables:
                    self.tables_tree.insert("", tk.END, text=table[0], values=table[0])
                conn.close()
                self.set_status("Tables loaded")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load tables: {str(e)}")

    def create_table_dialog(self):
        if not self.current_db:
            messagebox.showwarning("Warning", "Please create or open a database first")
            return

        self.table_dialog = tk.Toplevel(self.root)
        self.table_dialog.title("Create Table")
        
        ttk.Label(self.table_dialog, text="Table Name:").grid(row=0, column=0, padx=5, pady=5)
        self.table_name_entry = ttk.Entry(self.table_dialog)
        self.table_name_entry.grid(row=0, column=1, padx=5, pady=5)

        self.columns = []
        self.add_column_fields()

        ttk.Button(self.table_dialog, text="Add Column", command=self.add_column_fields).grid(row=999, column=0, pady=10)
        ttk.Button(self.table_dialog, text="Create Table", command=self.create_table).grid(row=999, column=1, pady=10)

    def add_column_fields(self, row=None):
        row = len(self.columns) + 1 if row is None else row
        column_frame = ttk.Frame(self.table_dialog)
        column_frame.grid(row=row, column=0, columnspan=2, sticky="ew")
        
        ttk.Label(column_frame, text="Column Name:").pack(side=tk.LEFT)
        name_entry = ttk.Entry(column_frame)
        name_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(column_frame, text="Data Type:").pack(side=tk.LEFT)
        type_combobox = ttk.Combobox(column_frame, values=["TEXT", "INTEGER", "REAL", "BLOB", "NULL"], state="readonly")
        type_combobox.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(column_frame, text="Constraints:").pack(side=tk.LEFT)
        constraints_entry = ttk.Entry(column_frame)
        constraints_entry.pack(side=tk.LEFT, padx=5)
        
        self.columns.append((name_entry, type_combobox, constraints_entry))

    def create_table(self):
        table_name = self.table_name_entry.get().strip()
        if not table_name:
            messagebox.showwarning("Warning", "Please enter a table name")
            return

        columns = []
        for col in self.columns:
            name = col[0].get().strip()
            dtype = col[1].get().strip()
            constraints = col[2].get().strip()
            if name and dtype:
                column_def = f"{name} {dtype} {constraints}".strip()
                columns.append(column_def)

        if not columns:
            messagebox.showwarning("Warning", "Please add at least one column")
            return

        try:
            conn = sqlite3.connect(self.current_db)
            cursor = conn.cursor()
            query = f"CREATE TABLE {table_name} ({', '.join(columns)})"
            cursor.execute(query)
            conn.commit()
            conn.close()
            self.load_tables()
            self.table_dialog.destroy()
            messagebox.showinfo("Success", "Table created successfully")
            self.set_status("Table created successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create table: {str(e)}")

    def delete_table(self):
        selected = self.tables_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a table to delete")
            return
        
        table_name = self.tables_tree.item(selected[0], "text")
        if messagebox.askyesno("Confirm", f"Delete table '{table_name}'?"):
            try:
                conn = sqlite3.connect(self.current_db)
                cursor = conn.cursor()
                cursor.execute(f"DROP TABLE {table_name}")
                conn.commit()
                conn.close()
                self.load_tables()
                messagebox.showinfo("Success", "Table deleted successfully")
                self.set_status("Table deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete table: {str(e)}")

    def load_table_data(self, event):
        selected = self.tables_tree.selection()
        if not selected:
            return
        
        self.current_table = self.tables_tree.item(selected[0], "text")
        self.data_tree.delete(*self.data_tree.get_children())
        
        try:
            conn = sqlite3.connect(self.current_db)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            
            self.data_tree["columns"] = columns
            self.data_tree["show"] = "headings"
            for col in columns:
                self.data_tree.heading(col, text=col)
                self.data_tree.column(col, width=100)
            
            cursor.execute(f"SELECT * FROM {self.current_table}")
            self.all_rows = cursor.fetchall()  # Store rows for searching/filtering
            for row in self.all_rows:
                self.data_tree.insert("", tk.END, values=row)
            
            conn.close()
            self.set_status("Table data loaded")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load table data: {str(e)}")

    # --------------------- Data Row Operations --------------------- #
    def add_data_dialog(self):
        if not self.current_table:
            messagebox.showwarning("Warning", "Please select a table first")
            return
        
        self.data_dialog = tk.Toplevel(self.root)
        self.data_dialog.title("Add Data")
        
        try:
            conn = sqlite3.connect(self.current_db)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns = cursor.fetchall()
            conn.close()
            
            self.data_entries = []
            for i, col in enumerate(columns):
                ttk.Label(self.data_dialog, text=col[1]).grid(row=i, column=0, padx=5, pady=2)
                entry = ttk.Entry(self.data_dialog)
                entry.grid(row=i, column=1, padx=5, pady=2)
                self.data_entries.append(entry)
            
            ttk.Button(self.data_dialog, text="Add", command=self.add_data).grid(row=len(columns), column=0, columnspan=2, pady=10)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load columns: {str(e)}")

    def add_data(self):
        try:
            conn = sqlite3.connect(self.current_db)
            cursor = conn.cursor()
            
            columns = []
            values = []
            for entry in self.data_entries:
                row = entry.grid_info()["row"]
                label_widgets = entry.master.grid_slaves(row=row, column=0)
                if label_widgets:
                    col_name = label_widgets[0]["text"]
                    columns.append(col_name)
                else:
                    continue
                values.append(entry.get())
            
            query = f"INSERT INTO {self.current_table} ({', '.join(columns)}) VALUES ({', '.join(['?']*len(values))})"
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            self.load_table_data(None)
            self.data_dialog.destroy()
            messagebox.showinfo("Success", "Data added successfully")
            self.set_status("Data added successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add data: {str(e)}")

    def edit_data_dialog(self):
        selected = self.data_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a record to edit")
            return
        
        self.edit_data_window = tk.Toplevel(self.root)
        self.edit_data_window.title("Edit Data")
        
        try:
            conn = sqlite3.connect(self.current_db)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns = [col[1] for col in cursor.fetchall()]
            values = self.data_tree.item(selected[0], "values")
            
            self.edit_entries = []
            for i, (col, val) in enumerate(zip(columns, values)):
                ttk.Label(self.edit_data_window, text=col).grid(row=i, column=0, padx=5, pady=2)
                entry = ttk.Entry(self.edit_data_window)
                entry.insert(0, val)
                entry.grid(row=i, column=1, padx=5, pady=2)
                self.edit_entries.append(entry)
            
            ttk.Button(self.edit_data_window, text="Update", 
                      command=lambda: self.update_data(selected[0])).grid(row=len(columns), column=0, columnspan=2, pady=10)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")

    def update_data(self, item_id):
        try:
            conn = sqlite3.connect(self.current_db)
            cursor = conn.cursor()
            
            columns = []
            for entry in self.edit_entries:
                row = entry.grid_info()["row"]
                label_widgets = self.edit_data_window.grid_slaves(row=row, column=0)
                if label_widgets:
                    columns.append(label_widgets[0]["text"])
            values = [entry.get() for entry in self.edit_entries]
            primary_key = self.get_primary_key()
            pk_value = self.data_tree.item(item_id, "values")[0]
            
            set_clause = ", ".join([f"{col} = ?" for col in columns])
            query = f"UPDATE {self.current_table} SET {set_clause} WHERE {primary_key} = ?"
            cursor.execute(query, values + [pk_value])
            conn.commit()
            conn.close()
            self.load_table_data(None)
            self.edit_data_window.destroy()
            messagebox.showinfo("Success", "Data updated successfully")
            self.set_status("Data updated successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update data: {str(e)}")

    def delete_data(self):
        selected = self.data_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a record to delete")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected record?"):
            try:
                conn = sqlite3.connect(self.current_db)
                cursor = conn.cursor()
                primary_key = self.get_primary_key()
                value = self.data_tree.item(selected[0], "values")[0]
                cursor.execute(f"DELETE FROM {self.current_table} WHERE {primary_key} = ?", (value,))
                conn.commit()
                conn.close()
                self.load_table_data(None)
                messagebox.showinfo("Success", "Data deleted successfully")
                self.set_status("Data deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete data: {str(e)}")

    def get_primary_key(self):
        try:
            conn = sqlite3.connect(self.current_db)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({self.current_table})")
            for col in cursor.fetchall():
                if col[5] == 1:
                    conn.close()
                    return col[1]
            conn.close()
            return "rowid"
        except Exception as e:
            return "rowid"

    # --------------------- Right-Click Context Menus --------------------- #
    # Table list sidebar (for table operations)
    def show_table_sidebar(self, event):
        row_id = self.tables_tree.identify_row(event.y)
        if not row_id:
            return
        self.tables_tree.selection_set(row_id)
        table_name = self.tables_tree.item(row_id, "text")
        
        if self.sidebar is not None and self.sidebar.winfo_exists():
            self.sidebar.destroy()
        self.sidebar = tk.Toplevel(self.root)
        self.sidebar.title(f"Table Options: {table_name}")
        self.sidebar.geometry("+{}+{}".format(event.x_root, event.y_root))
        self.sidebar.attributes("-topmost", True)
        
        ttk.Button(self.sidebar, text="Edit Table Name", command=lambda: self.edit_table_name(table_name)).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(self.sidebar, text="View Table Schema", command=lambda: self.edit_table_schema(table_name)).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(self.sidebar, text="Delete Table", command=lambda: self.delete_table_by_sidebar(table_name)).pack(fill=tk.X, padx=10, pady=5)

    def delete_table_by_sidebar(self, table_name):
        if messagebox.askyesno("Confirm", f"Delete table '{table_name}'?"):
            try:
                conn = sqlite3.connect(self.current_db)
                cursor = conn.cursor()
                cursor.execute(f"DROP TABLE {table_name}")
                conn.commit()
                conn.close()
                self.load_tables()
                messagebox.showinfo("Success", "Table deleted successfully")
                if self.sidebar is not None:
                    self.sidebar.destroy()
                self.set_status("Table deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete table: {str(e)}")

    def edit_table_name(self, old_name):
        new_name = simpledialog.askstring("Edit Table Name", f"Enter new name for table '{old_name}':")
        if new_name and new_name.strip():
            try:
                conn = sqlite3.connect(self.current_db)
                cursor = conn.cursor()
                cursor.execute(f"ALTER TABLE {old_name} RENAME TO {new_name.strip()}")
                conn.commit()
                conn.close()
                self.load_tables()
                messagebox.showinfo("Success", f"Table renamed to '{new_name.strip()}'")
                if self.sidebar is not None:
                    self.sidebar.destroy()
                self.set_status("Table renamed successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename table: {str(e)}")

    def edit_table_schema(self, table_name):
        try:
            conn = sqlite3.connect(self.current_db)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            schema_info = cursor.fetchall()
            conn.close()
            
            schema_text = f"Schema for table '{table_name}':\n\n"
            schema_text += "cid | name | type | notnull | dflt_value | pk\n"
            schema_text += "-" * 50 + "\n"
            for col in schema_info:
                schema_text += " | ".join(str(item) for item in col) + "\n"
            
            schema_window = tk.Toplevel(self.root)
            schema_window.title(f"Schema of {table_name}")
            text_widget = scrolledtext.ScrolledText(schema_window, width=60, height=15)
            text_widget.pack(fill=tk.BOTH, expand=True)
            text_widget.insert(tk.END, schema_text)
            text_widget.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve schema: {str(e)}")

    # Data row context menu (right-click on data rows)
    def show_data_context_menu(self, event):
        row_id = self.data_tree.identify_row(event.y)
        if not row_id:
            return
        self.data_tree.selection_set(row_id)
        if self.data_context_menu is None:
            self.data_context_menu = tk.Menu(self.root, tearoff=0)
            self.data_context_menu.add_command(label="Edit Row", command=self.edit_data_dialog)
            self.data_context_menu.add_command(label="Delete Row", command=self.delete_data)
            self.data_context_menu.add_separator()
            self.data_context_menu.add_command(label="Export Table to CSV", command=self.export_table_csv)
        self.data_context_menu.post(event.x_root, event.y_root)

    # --------------------- Additional Features --------------------- #
    def export_table_csv(self):
        if not self.current_table:
            messagebox.showwarning("Warning", "Please select a table first")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")],
                                                 title="Export Table to CSV")
        if file_path:
            try:
                conn = sqlite3.connect(self.current_db)
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {self.current_table}")
                rows = cursor.fetchall()
                cursor.execute(f"PRAGMA table_info({self.current_table})")
                headers = [col[1] for col in cursor.fetchall()]
                conn.close()
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(rows)
                messagebox.showinfo("Success", f"Data exported to {file_path}")
                self.set_status("Data exported to CSV")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def run_query_window(self):
        if not self.current_db:
            messagebox.showwarning("Warning", "Please open a database first")
            return

        query_win = tk.Toplevel(self.root)
        query_win.title("Run SQL Query")
        
        # Query input
        ttk.Label(query_win, text="Enter SQL Query:").pack(padx=5, pady=5)
        query_text = scrolledtext.ScrolledText(query_win, width=80, height=10)
        query_text.pack(padx=5, pady=5)
        
        # Results display
        ttk.Label(query_win, text="Results:").pack(padx=5, pady=5)
        results_text = scrolledtext.ScrolledText(query_win, width=80, height=15)
        results_text.pack(padx=5, pady=5)
        results_text.configure(state="disabled")
        
        def execute_query():
            sql = query_text.get("1.0", tk.END).strip()
            if not sql:
                messagebox.showwarning("Warning", "Please enter a SQL query")
                return
            try:
                conn = sqlite3.connect(self.current_db)
                cursor = conn.cursor()
                cursor.execute(sql)
                # If it's a SELECT query, fetch results
                if sql.lower().startswith("select"):
                    rows = cursor.fetchall()
                    headers = [description[0] for description in cursor.description]
                    output = "\t".join(headers) + "\n" + "-" * 50 + "\n"
                    for row in rows:
                        output += "\t".join(str(item) for item in row) + "\n"
                else:
                    conn.commit()
                    output = "Query executed successfully."
                conn.close()
                results_text.configure(state="normal")
                results_text.delete("1.0", tk.END)
                results_text.insert(tk.END, output)
                results_text.configure(state="disabled")
                self.set_status("Query executed")
            except Exception as e:
                messagebox.showerror("Error", f"Query failed: {str(e)}")
        
        ttk.Button(query_win, text="Run Query", command=execute_query).pack(pady=5)

    def show_tutorial(self):
        tutorial_window = tk.Toplevel(self.root)
        tutorial_window.title("Tutorial")
        tutorial_text = scrolledtext.ScrolledText(tutorial_window, width=80, height=25)
        tutorial_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tutorial_content = (
            "SQLite Tutorial\n"
            "----------------\n\n"
            "Data Types:\n"
            " - TEXT: Used for text strings.\n"
            " - INTEGER: Used for whole numbers.\n"
            " - REAL: Used for floating-point numbers.\n"
            " - BLOB: Used for binary data.\n"
            " - NULL: Represents a NULL value.\n\n"
            "Constraints:\n"
            " - PRIMARY KEY: Uniquely identifies each record.\n"
            " - NOT NULL: Ensures a column cannot have a NULL value.\n"
            " - UNIQUE: Ensures all values in a column are different.\n"
            " - CHECK: Ensures values satisfy a specified condition.\n"
            " - DEFAULT: Sets a default value if none is provided.\n\n"
            "Extra Features:\n"
            " - Run Query: Execute arbitrary SQL queries against the current database.\n"
            " - Backup Database: Create a backup copy of the current database file.\n"
            " - Import CSV: Import data from a CSV file into the selected table.\n"
            " - Export to CSV: Export table data to a CSV file for use in spreadsheets.\n"
            " - Refresh: Quickly update the tables and data views.\n"
            " - Search: Filter data rows by keywords.\n\n"
            "Usage:\n"
            "This SQLite Database Manager allows you to create and manage databases, tables, and data.\n"
            "Right-click on table names or data rows to access context-specific options.\n"
        )
        tutorial_text.insert(tk.END, tutorial_content)
        tutorial_text.configure(state="disabled")
    
    # --------------------- Data Filtering (Search Feature) --------------------- #
    def filter_data(self, event):
        """Filters displayed data rows based on search input."""
        if not hasattr(self, 'all_rows'):
            return
        
        search_term = self.search_var.get().lower()
        # Clear current displayed rows
        self.data_tree.delete(*self.data_tree.get_children())
        for row in self.all_rows:
            # If search term is empty or is found in any cell, display the row
            if not search_term or any(search_term in str(cell).lower() for cell in row):
                self.data_tree.insert("", tk.END, values=row)

if __name__ == "__main__":
    root = tk.Tk()
    app = DataManager(root)
    root.mainloop()
