#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Media Captioning Tool - Main Application Class
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json

from app.media_viewer import MediaViewer
from app.project_manager import ProjectManager
from app.ui_components import FileListPanel, ControlPanel

class MediaCaptioningApp:
    def __init__(self, master):
        self.master = master
        self.current_project = None
        self.current_media = None
        
        # Initialize components
        self.project_manager = ProjectManager(self)
        
        # Create main frame
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create menu
        self.create_menu()
        
        # Create layout
        self.create_layout()
        
        # Initialize state
        self.update_ui_state()
    
    def create_menu(self):
        """Create the application menu"""
        menubar = tk.Menu(self.master)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_project)
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_command(label="Save Project As", command=self.save_project_as)
        file_menu.add_command(label="Exit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Set Media Path", command=self.set_media_path)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # Export menu
        export_menu = tk.Menu(menubar, tearoff=0)
        export_menu.add_command(label="Export", command=self.show_export_dialog)
        menubar.add_cascade(label="Export", menu=export_menu)
                
        self.master.config(menu=menubar)
    
    def create_layout(self):
        """Create the main application layout"""
        # Create main panels
        self.left_panel = ttk.Frame(self.main_frame, width=200)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        self.center_panel = ttk.Frame(self.main_frame)
        self.center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_panel = ttk.Frame(self.main_frame, width=200)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Center panel - Media viewer and caption editor
        self.media_viewer = MediaViewer(self.center_panel, self)
        self.media_viewer.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Caption editor
        caption_frame = ttk.LabelFrame(self.center_panel, text="Caption")
        caption_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.caption_text = tk.Text(caption_frame, height=4, wrap=tk.WORD)
        self.caption_text.pack(fill=tk.X, padx=5, pady=5)
        self.caption_text.bind("<KeyRelease>", self.on_caption_change)
        
        # Right panel - File list
        self.file_list_panel = FileListPanel(self.right_panel, self)
        self.file_list_panel.pack(fill=tk.BOTH, expand=True)
        
        # Bottom panel - Controls
        self.control_panel = ControlPanel(self.center_panel, self)
        self.control_panel.pack(fill=tk.X, pady=(5, 0))
    
    def update_ui_state(self):
        """Update UI state based on current project and media"""
        has_project = self.current_project is not None
        has_media = self.current_media is not None
        
        # Update file list
        if has_project and 'media_path' in self.current_project:
            self.file_list_panel.load_files(self.current_project['media_path'])
        else:
            self.file_list_panel.clear()
        
        # Update caption
        if has_media:
            caption = self.current_media.get('caption', '')
            self.caption_text.delete(1.0, tk.END)
            self.caption_text.insert(tk.END, caption)
        else:
            self.caption_text.delete(1.0, tk.END)
        
        # Update control panel
        self.control_panel.update_ui()
    
    def new_project(self):
        """Create a new project"""
        if self.current_project:
            if not messagebox.askyesno("New Project", "Any unsaved changes will be lost. Continue?"):
                return
        
        self.current_project = {
            'name': 'Untitled Project',
            'media_path': '',
            'media_files': {}
        }
        self.current_media = None
        self.update_ui_state()
    
    def open_project(self):
        """Open an existing project"""
        file_path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            self.project_manager.load_project(file_path)
    
    def save_project(self):
        """Save the current project"""
        if not self.current_project:
            messagebox.showerror("Error", "No project is currently open")
            return
        
        if 'file_path' in self.current_project:
            self.project_manager.save_project(self.current_project['file_path'])
        else:
            self.save_project_as()
    
    def save_project_as(self):
        """Save the current project with a new name"""
        if not self.current_project:
            messagebox.showerror("Error", "No project is currently open")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Project As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            self.project_manager.save_project(file_path)
    
    def show_export_dialog(self):
        """Show the unified export dialog"""
        if not self.current_project:
            messagebox.showerror("Error", "No project is currently open")
            return
        
        # Create dialog window
        dialog = tk.Toplevel(self.master)
        dialog.title("Export Options")
        dialog.geometry("500x550")
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Create main frame with padding
        main_frame = ttk.Frame(dialog, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Get saved export settings or use defaults
        export_settings = self.current_project.get('export_settings', {})
        
        # Variables for form fields
        export_media_var = tk.BooleanVar(value=export_settings.get('export_media', False))
        export_media_path_var = tk.StringVar(value=export_settings.get('export_media_path', os.path.join(os.path.expanduser("~"), "exported_media")))
        
        export_captions_var = tk.BooleanVar(value=export_settings.get('export_captions', False))
        export_captions_path_var = tk.StringVar(value=export_settings.get('export_captions_path', os.path.join(os.path.expanduser("~"), "exported_captions")))
        use_media_folder_var = tk.BooleanVar(value=export_settings.get('use_media_folder', False))
        
        # Helper function to update UI state
        def update_ui_state():
            # Media export options
            media_path_entry.config(state=tk.NORMAL if export_media_var.get() else tk.DISABLED)
            media_path_button.config(state=tk.NORMAL if export_media_var.get() else tk.DISABLED)
            
            # Caption export options
            captions_path_entry.config(state=tk.NORMAL if export_captions_var.get() and not use_media_folder_var.get() else tk.DISABLED)
            captions_path_button.config(state=tk.NORMAL if export_captions_var.get() and not use_media_folder_var.get() else tk.DISABLED)
            use_media_folder_cb.config(state=tk.NORMAL if export_captions_var.get() and export_media_var.get() else tk.DISABLED)
        
        # Helper function to browse for directory
        def browse_directory(path_var):
            directory = filedialog.askdirectory(title="Select Export Directory")
            if directory:
                path_var.set(directory)
        
        # Media export section
        media_frame = ttk.LabelFrame(main_frame, text="Media Export", padding="10 10 10 10")
        media_frame.pack(fill=tk.X, pady=(0, 10))
        
        media_cb = ttk.Checkbutton(media_frame, text="Export Media", variable=export_media_var, command=update_ui_state)
        media_cb.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(media_frame, text="Export Path:").grid(row=1, column=0, sticky=tk.W, pady=2)
        media_path_entry = ttk.Entry(media_frame, textvariable=export_media_path_var, width=40)
        media_path_entry.grid(row=1, column=1, sticky=tk.W, pady=2)
        media_path_button = ttk.Button(media_frame, text="Browse...", 
                                       command=lambda: browse_directory(export_media_path_var))
        media_path_button.grid(row=1, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        
        # Captions export section
        captions_frame = ttk.LabelFrame(main_frame, text="Captions Export", padding="10 10 10 10")
        captions_frame.pack(fill=tk.X, pady=(0, 10))
        
        captions_cb = ttk.Checkbutton(captions_frame, text="Export Captions", variable=export_captions_var, command=update_ui_state)
        captions_cb.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        use_media_folder_cb = ttk.Checkbutton(captions_frame, text="Use Media Export Folder", 
                                             variable=use_media_folder_var, command=update_ui_state)
        use_media_folder_cb.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(captions_frame, text="Export Path:").grid(row=2, column=0, sticky=tk.W, pady=2)
        captions_path_entry = ttk.Entry(captions_frame, textvariable=export_captions_path_var, width=40)
        captions_path_entry.grid(row=2, column=1, sticky=tk.W, pady=2)
        captions_path_button = ttk.Button(captions_frame, text="Browse...", 
                                         command=lambda: browse_directory(export_captions_path_var))
        captions_path_button.grid(row=2, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        
        def perform_export():
            # Validate that at least one export option is selected
            if not any([export_media_var.get(), export_captions_var.get()]):
                messagebox.showerror("Error", "Please select at least one export option")
                return
            
            # Save export settings
            self.current_project.setdefault('export_settings', {}).update({
                'export_media': export_media_var.get(),
                'export_media_path': export_media_path_var.get(),
                'export_captions': export_captions_var.get(),
                'export_captions_path': export_captions_path_var.get(),
                'use_media_folder': use_media_folder_var.get()
            })
            
            # Prepare export paths
            media_export_path = export_media_path_var.get() if export_media_var.get() else None
            
            if export_captions_var.get():
                if use_media_folder_var.get() and export_media_var.get():
                    captions_export_path = media_export_path
                else:
                    captions_export_path = export_captions_path_var.get()
            else:
                captions_export_path = None
            
            # Create directories if they don't exist
            for path in [p for p in [media_export_path, captions_export_path] if p]:
                os.makedirs(path, exist_ok=True)
            
            # Perform exports
            try:
                if export_media_var.get():
                    self.export_media(media_export_path)
                
                if export_captions_var.get():
                    self.export_captions(captions_export_path)
                
                messagebox.showinfo("Success", "Export completed successfully!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")
        
        ttk.Button(button_frame, text="Export", command=perform_export).pack(side=tk.RIGHT)
        
        # Initialize UI state
        update_ui_state()
        
        # Center the dialog on the screen
        self.center_window(dialog)
        
        # Wait for the dialog to be closed
        dialog.wait_window()
    
    def export_media(self, export_path):
        """Export media files"""
        import shutil
        
        # Copy all media files referenced in the project
        for media_id in self.current_project.get('media_files', {}):
            source_path = os.path.join(self.current_project['media_path'], media_id)
            dest_path = os.path.join(export_path, media_id)
            
            if os.path.exists(source_path):
                shutil.copy2(source_path, dest_path)
    
    def export_captions(self, export_path):
        """Export captions to text files"""
        # Export captions as text files
        for media_id, media_info in self.current_project.get('media_files', {}).items():
            caption = media_info.get('caption', '')
            if caption:
                caption_filename = f"{os.path.splitext(media_id)[0]}.txt"
                caption_path = os.path.join(export_path, caption_filename)
                
                with open(caption_path, 'w', encoding='utf-8') as f:
                    f.write(caption)
    
    def set_media_path(self):
        """Set the media path for the current project"""
        if not self.current_project:
            messagebox.showerror("Error", "No project is currently open")
            return
        
        media_path = filedialog.askdirectory(title="Select Media Directory")
        if media_path:
            self.current_project['media_path'] = media_path
            self.update_ui_state()
    
    def select_media(self, media_id):
        """Select a media file to display"""
        if not self.current_project or not media_id:
            return
        
        # Save current caption if there's a current media
        if self.current_media:
            self.current_media['caption'] = self.caption_text.get(1.0, tk.END).strip()
        
        # Get or create media entry
        if media_id not in self.current_project['media_files']:
            self.current_project['media_files'][media_id] = {
                'id': media_id,
                'caption': ''
            }
        
        self.current_media = self.current_project['media_files'][media_id]
        
        # Update UI
        self.media_viewer.load_media(os.path.join(self.current_project['media_path'], media_id))
        self.update_ui_state()
    
    def on_caption_change(self, event=None):
        """Handle caption text changes"""
        if self.current_media:
            self.current_media['caption'] = self.caption_text.get(1.0, tk.END).strip()
    
    def center_window(self, window):
        """Center a window on the screen"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}') 