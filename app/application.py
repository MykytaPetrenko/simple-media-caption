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
from app.mask_manager import MaskManager
from app.ui_components import FileListPanel, MaskListPanel, ControlPanel
from app.tracking import track_points_with_lk_and_kalman

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
        
        # Left panel - Mask list
        self.mask_list_panel = MaskListPanel(self.left_panel, self)
        self.mask_list_panel.pack(fill=tk.BOTH, expand=True)
        
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
        
        # Initialize mask manager
        self.mask_manager = MaskManager(self, self.media_viewer.canvas)
    
    def update_ui_state(self):
        """Update UI state based on current project and media"""
        has_project = self.current_project is not None
        has_media = self.current_media is not None
        
        # Update file list
        if has_project and 'media_path' in self.current_project:
            self.file_list_panel.load_files(self.current_project['media_path'])
        else:
            self.file_list_panel.clear()
        
        # Update mask list
        if has_media:
            media_id = self.current_media['id']
            masks = self.current_project.get('masks', {}).get(media_id, [])
            self.mask_list_panel.update_mask_list(masks)
            
            # Draw masks for the current media
            self.mask_manager.draw_all_masks()
        else:
            self.mask_list_panel.clear()
        
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
            'media_files': {},
            'masks': {}
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
        
        export_masks_var = tk.BooleanVar(value=export_settings.get('export_masks', False))
        export_masks_path_var = tk.StringVar(value=export_settings.get('export_masks_path', os.path.join(os.path.expanduser("~"), "exported_masks")))
        mask_offset_var = tk.IntVar(value=export_settings.get('mask_offset', 0))
        blur_mask_var = tk.BooleanVar(value=export_settings.get('blur_mask', False))
        blur_amount_var = tk.IntVar(value=export_settings.get('blur_amount', 3))
        mask_intensity_var = tk.IntVar(value=export_settings.get('mask_intensity', 255))
        invert_mask_var = tk.BooleanVar(value=export_settings.get('invert_mask', False))
        
        # Helper function to update UI state
        def update_ui_state():
            # Media export options
            media_path_entry.config(state=tk.NORMAL if export_media_var.get() else tk.DISABLED)
            media_path_button.config(state=tk.NORMAL if export_media_var.get() else tk.DISABLED)
            
            # Caption export options
            captions_path_entry.config(state=tk.NORMAL if export_captions_var.get() and not use_media_folder_var.get() else tk.DISABLED)
            captions_path_button.config(state=tk.NORMAL if export_captions_var.get() and not use_media_folder_var.get() else tk.DISABLED)
            use_media_folder_cb.config(state=tk.NORMAL if export_captions_var.get() and export_media_var.get() else tk.DISABLED)
            
            # Mask export options
            masks_path_entry.config(state=tk.NORMAL if export_masks_var.get() else tk.DISABLED)
            masks_path_button.config(state=tk.NORMAL if export_masks_var.get() else tk.DISABLED)
            mask_offset_entry.config(state=tk.NORMAL if export_masks_var.get() else tk.DISABLED)
            blur_mask_cb.config(state=tk.NORMAL if export_masks_var.get() else tk.DISABLED)
            blur_amount_entry.config(state=tk.NORMAL if export_masks_var.get() and blur_mask_var.get() else tk.DISABLED)
            mask_intensity_entry.config(state=tk.NORMAL if export_masks_var.get() else tk.DISABLED)
            invert_mask_cb.config(state=tk.NORMAL if export_masks_var.get() else tk.DISABLED)
        
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
        
        # Masks export section
        masks_frame = ttk.LabelFrame(main_frame, text="Masks Export", padding="10 10 10 10")
        masks_frame.pack(fill=tk.X, pady=(0, 10))
        
        masks_cb = ttk.Checkbutton(masks_frame, text="Export Masks", variable=export_masks_var, command=update_ui_state)
        masks_cb.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(masks_frame, text="Export Path:").grid(row=1, column=0, sticky=tk.W, pady=2)
        masks_path_entry = ttk.Entry(masks_frame, textvariable=export_masks_path_var, width=40)
        masks_path_entry.grid(row=1, column=1, sticky=tk.W, pady=2)
        masks_path_button = ttk.Button(masks_frame, text="Browse...", 
                                      command=lambda: browse_directory(export_masks_path_var))
        masks_path_button.grid(row=1, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        
        ttk.Label(masks_frame, text="Mask Offset (px):").grid(row=2, column=0, sticky=tk.W, pady=2)
        mask_offset_entry = ttk.Spinbox(masks_frame, from_=-50, to=50, textvariable=mask_offset_var, width=5)
        mask_offset_entry.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        blur_mask_cb = ttk.Checkbutton(masks_frame, text="Blur Mask", variable=blur_mask_var, command=update_ui_state)
        blur_mask_cb.grid(row=3, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(masks_frame, text="Blur Amount (px):").grid(row=4, column=0, sticky=tk.W, pady=2)
        blur_amount_entry = ttk.Spinbox(masks_frame, from_=1, to=20, textvariable=blur_amount_var, width=5)
        blur_amount_entry.grid(row=4, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(masks_frame, text="Mask Intensity (0-255):").grid(row=5, column=0, sticky=tk.W, pady=2)
        mask_intensity_entry = ttk.Spinbox(masks_frame, from_=0, to=255, textvariable=mask_intensity_var, width=5)
        mask_intensity_entry.grid(row=5, column=1, sticky=tk.W, pady=2)
        
        invert_mask_cb = ttk.Checkbutton(masks_frame, text="Invert Mask", variable=invert_mask_var)
        invert_mask_cb.grid(row=6, column=0, sticky=tk.W, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        
        def perform_export():
            # Validate that at least one export option is selected
            if not any([export_media_var.get(), export_captions_var.get(), export_masks_var.get()]):
                messagebox.showerror("Error", "Please select at least one export option")
                return
            
            # Save export settings
            self.current_project.setdefault('export_settings', {}).update({
                'export_media': export_media_var.get(),
                'export_media_path': export_media_path_var.get(),
                'export_captions': export_captions_var.get(),
                'export_captions_path': export_captions_path_var.get(),
                'use_media_folder': use_media_folder_var.get(),
                'export_masks': export_masks_var.get(),
                'export_masks_path': export_masks_path_var.get(),
                'mask_offset': mask_offset_var.get(),
                'blur_mask': blur_mask_var.get(),
                'blur_amount': blur_amount_var.get(),
                'mask_intensity': mask_intensity_var.get(),
                'invert_mask': invert_mask_var.get()
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
            
            masks_export_path = export_masks_path_var.get() if export_masks_var.get() else None
            
            # Create directories if they don't exist
            for path in [p for p in [media_export_path, captions_export_path, masks_export_path] if p]:
                os.makedirs(path, exist_ok=True)
            
            # Perform exports
            try:
                if export_media_var.get():
                    self.export_media(media_export_path)
                
                if export_captions_var.get():
                    self.export_captions(captions_export_path)
                
                if export_masks_var.get():
                    self.export_masks_advanced(
                        masks_export_path,
                        mask_offset_var.get(),
                        blur_mask_var.get(),
                        blur_amount_var.get(),
                        mask_intensity_var.get(),
                        invert_mask_var.get()
                    )
                
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
    
    def export_masks_advanced(self, export_path, mask_offset=0, blur_mask=False, blur_amount=3, 
                             mask_intensity=255, invert_mask=False):
        """Export masks with advanced options"""
        import cv2
        import numpy as np
        from PIL import Image, ImageDraw, ImageFilter
        
        # Process each media file that has masks
        for media_id, masks in self.current_project.get('masks', {}).items():
            if not masks:  # Skip if no masks for this media
                continue
                
            # Get the original media file path
            media_path = os.path.join(self.current_project['media_path'], media_id)
            if not os.path.exists(media_path):
                messagebox.showwarning("Warning", f"Media file not found: {media_id}")
                continue
            
            # Determine if it's an image or video
            is_video = media_id.lower().endswith(('.mp4', '.avi', '.mov'))
            
            if is_video:
                # Process video
                cap = cv2.VideoCapture(media_path)
                if not cap.isOpened():
                    messagebox.showwarning("Warning", f"Could not open video: {media_id}")
                    continue
                
                # Get video properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                # Create output video writer
                mask_path = os.path.join(export_path, f"{os.path.splitext(media_id)[0]}_mask.mp4")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(mask_path, fourcc, fps, (width, height), False)
                
                # Create progress dialog
                progress_window = tk.Toplevel(self.master)
                progress_window.title("Exporting Video Masks")
                progress_window.geometry("300x100")
                progress_window.transient(self.master)
                progress_window.grab_set()
                
                progress_label = ttk.Label(progress_window, text=f"Processing {media_id}...")
                progress_label.pack(pady=10)
                
                progress_var = tk.DoubleVar()
                progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
                progress_bar.pack(fill=tk.X, padx=20, pady=10)
                
                # Center the progress window
                self.center_window(progress_window)
                
                # Update UI
                self.master.update()
                
                try:
                    # Process each frame
                    frame_idx = 0
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        
                        # Create mask frame
                        mask_frame = np.zeros((height, width), dtype=np.uint8)
                        
                        # Draw all masks for this frame
                        for mask in masks:
                            points = self.mask_manager.get_interpolated_points(mask, frame_idx)
                            if points and len(points) >= 3:
                                # Apply offset to points if needed
                                if mask_offset != 0:
                                    points = self._offset_polygon(points, mask_offset)
                                
                                # Convert points to numpy array
                                points = np.array(points, dtype=np.int32)
                                # Fill the polygon with white (or specified intensity)
                                cv2.fillPoly(mask_frame, [points], mask_intensity)
                        
                        # Apply blur if requested
                        if blur_mask and blur_amount > 0:
                            mask_frame = cv2.GaussianBlur(mask_frame, (blur_amount*2+1, blur_amount*2+1), 0)
                        
                        # Invert mask if requested
                        if invert_mask:
                            mask_frame = cv2.bitwise_not(mask_frame)
                        
                        # Write the mask frame
                        out.write(mask_frame)
                        frame_idx += 1
                        
                        # Update progress
                        progress_var.set((frame_idx / total_frames) * 100)
                        progress_window.update()
                    
                    # Release video resources
                    cap.release()
                    out.release()
                    
                finally:
                    # Close progress window
                    progress_window.destroy()
                
            else:
                # Process image
                # Open the image to get dimensions
                img = Image.open(media_path)
                width, height = img.size
                
                # Create a new black image
                mask_img = Image.new('L', (width, height), 0)
                draw = ImageDraw.Draw(mask_img)
                
                # Draw all masks
                for mask in masks:
                    points = mask.get('points', [])
                    if points and len(points) >= 3:
                        # Apply offset to points if needed
                        if mask_offset != 0:
                            points = self._offset_polygon(points, mask_offset)
                        
                        # Convert points to flat list for PIL
                        flat_points = [coord for point in points for coord in point]
                        # Fill the polygon with white (or specified intensity)
                        draw.polygon(flat_points, fill=mask_intensity)
                
                # Apply blur if requested
                if blur_mask and blur_amount > 0:
                    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=blur_amount))
                
                # Invert mask if requested
                if invert_mask:
                    mask_img = ImageOps.invert(mask_img)
                
                # Save the mask image
                mask_path = os.path.join(export_path, f"{os.path.splitext(media_id)[0]}_mask{os.path.splitext(media_id)[1]}")
                mask_img.save(mask_path)
    
    def _offset_polygon(self, points, offset):
        """Offset polygon points by the given amount (positive=expand, negative=shrink)"""
        if offset == 0 or len(points) < 3:
            return points
            
        import numpy as np
        
        # Convert to numpy array
        points_array = np.array(points)
        
        # Calculate centroid
        centroid = np.mean(points_array, axis=0)
        
        # Calculate vectors from centroid to each point
        vectors = points_array - centroid
        
        # Normalize vectors
        norms = np.sqrt(np.sum(vectors**2, axis=1))
        normalized_vectors = vectors / norms[:, np.newaxis]
        
        # Apply offset
        offset_points = points_array + normalized_vectors * offset
        
        # Convert back to list of tuples
        return [(int(x), int(y)) for x, y in offset_points]
    
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
        
        # Deactivate any active mask tools
        if hasattr(self, 'mask_manager'):
            self.mask_manager.deactivate_tools()
            if hasattr(self, 'mask_list_panel'):
                self.mask_list_panel.set_editing_mode(False)
        
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
    
    def activate_create_mask_tool(self):
        """Activate the create mask tool"""
        if not self.current_media:
            messagebox.showerror("Error", "No media selected")
            return
        
        self.mask_manager.activate_create_mask_tool()
    
    def activate_keyframe_mask_tool(self, mask=None):
        """Activate the keyframe mask tool"""
        if not self.current_media:
            messagebox.showerror("Error", "No media selected")
            return
        
        if not self.media_viewer.is_video:
            messagebox.showerror("Error", "Keyframes can only be added to video files")
            return
        
        if mask is None:
            selected_mask = self.mask_list_panel.get_selected_mask()
            if not selected_mask:
                messagebox.showerror("Error", "No mask selected")
                return
            mask = selected_mask
        
        self.mask_manager.activate_keyframe_mask_tool(mask)
    
    def add_mask(self, points):
        """Add a new mask to the current media"""
        if not self.current_media:
            return
        
        media_id = self.current_media['id']
        
        if media_id not in self.current_project.get('masks', {}):
            self.current_project.setdefault('masks', {})[media_id] = []
        
        mask_id = f"mask_{len(self.current_project['masks'][media_id]) + 1}"
        
        new_mask = {
            'id': mask_id,
            'keyframes': [{
                'frame': 0,  # First keyframe at frame 0
                'points': points
            }]
        }
        
        self.current_project['masks'][media_id].append(new_mask)
        self.update_ui_state()
        
        return new_mask
    
    def add_keyframe(self, mask_id, points, frame):
        """Add a new keyframe to an existing mask"""
        if not self.current_media:
            return
        
        media_id = self.current_media['id']
        
        for mask in self.current_project['masks'].get(media_id, []):
            if mask['id'] == mask_id:
                # Add new keyframe with the current frame number
                mask['keyframes'].append({
                    'frame': frame,  # Use the actual current frame number
                    'points': points
                })
                # Sort keyframes by frame number
                mask['keyframes'].sort(key=lambda k: k['frame'])
                break
        
        self.update_ui_state()
    
    def delete_mask(self, mask_id):
        """Delete a mask"""
        if not self.current_media:
            return
        
        media_id = self.current_media['id']
        
        masks = self.current_project['masks'].get(media_id, [])
        self.current_project['masks'][media_id] = [m for m in masks if m['id'] != mask_id]
        
        self.update_ui_state()
    
    def track_mask(self, mask_id):
        """Track mask vertices across frames and create keyframes"""
        
        if not self.current_media:
            messagebox.showerror("Error", "No valid media selected")
            return
        
        # Check if media is a video
        if not self.media_viewer.is_video:
            messagebox.showerror("Error", "Tracking only works with videos")
            return
        
        media_path = self.media_viewer.media_path
        # Find the mask
        media_id = self.current_media['id']
        mask = None
        for m in self.current_project['masks'].get(media_id, []):
            if m['id'] == mask_id:
                mask = m
                break
        
        if not mask or not mask['keyframes']:
            messagebox.showerror("Error", "No valid mask selected")
            return
        
        # Get initial points from the first keyframe
        initial_points = mask['keyframes'][0]['points']
        
        # Show tracking configuration dialog
        tracking_config = self.show_tracking_config_dialog()
        if not tracking_config:
            return  # User cancelled
        
        # Show progress dialog
        progress_window = tk.Toplevel(self.master)
        progress_window.title("Tracking Progress")
        progress_window.geometry("300x100")
        progress_window.transient(self.master)
        progress_window.grab_set()
        
        progress_label = ttk.Label(progress_window, text="Tracking mask vertices...")
        progress_label.pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        # Center the progress window
        self.center_window(progress_window)
        
        # Update UI
        self.master.update()
        
        try:
            # Track points across frames with the configured parameters
            tracked_points = self.track_points_with_config(media_path, initial_points, tracking_config)
            
            # Clear existing keyframes except the first one
            first_keyframe = mask['keyframes'][0]
            mask['keyframes'] = [first_keyframe]
            
            # Add keyframes for each frame
            for frame_idx, points in enumerate(tracked_points):
                if frame_idx == 0:  # Skip first frame as we already have it
                    continue
                    
                # Skip frames with None points
                if None in points:
                    continue
                    
                # Add keyframe
                mask['keyframes'].append({
                    'frame': frame_idx,
                    'points': points
                })
                
                # Update progress
                progress_var.set((frame_idx / len(tracked_points)) * 100)
                progress_window.update()
            
            # Sort keyframes by frame number
            mask['keyframes'].sort(key=lambda k: k['frame'])
            
            # Update UI
            self.update_ui_state()
            
            messagebox.showinfo("Tracking Complete", f"Added {len(mask['keyframes']) - 1} keyframes")
            
        except Exception as e:
            messagebox.showerror("Error", f"Tracking failed: {str(e)}")
        finally:
            # Close progress window
            progress_window.destroy()
    
    def show_tracking_config_dialog(self):
        """Show dialog for configuring tracking parameters"""
        # Create dialog window
        dialog = tk.Toplevel(self.master)
        dialog.title("Tracking Configuration")
        dialog.geometry("450x400")
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Create main frame with padding
        main_frame = ttk.Frame(dialog, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Get saved tracking settings or use defaults
        tracking_settings = self.current_project.get('tracking_settings', {})
        
        # Variables for form fields
        use_shifted_points_var = tk.BooleanVar(value=tracking_settings.get('use_shifted_points', True))
        shift_value_var = tk.IntVar(value=tracking_settings.get('shift_value', 5))
        
        use_window1_var = tk.BooleanVar(value=tracking_settings.get('use_window1', True))
        window1_size_var = tk.IntVar(value=tracking_settings.get('window1_size', 21))
        
        use_window2_var = tk.BooleanVar(value=tracking_settings.get('use_window2', False))
        window2_size_var = tk.IntVar(value=tracking_settings.get('window2_size', 31))
        
        use_window3_var = tk.BooleanVar(value=tracking_settings.get('use_window3', False))
        window3_size_var = tk.IntVar(value=tracking_settings.get('window3_size', 41))
        
        filter_method_var = tk.StringVar(value=tracking_settings.get('filter_method', "consensus"))
        
        # Result variable
        result = {"cancelled": True}
        
        # Helper function to update UI state
        def update_ui_state():
            shift_value_entry.config(state=tk.NORMAL if use_shifted_points_var.get() else tk.DISABLED)
            
            window1_size_entry.config(state=tk.NORMAL if use_window1_var.get() else tk.DISABLED)
            window2_size_entry.config(state=tk.NORMAL if use_window2_var.get() else tk.DISABLED)
            window3_size_entry.config(state=tk.NORMAL if use_window3_var.get() else tk.DISABLED)
        
        # Sample points section
        sample_frame = ttk.LabelFrame(main_frame, text="Sample Points", padding="10 10 10 10")
        sample_frame.pack(fill=tk.X, pady=(0, 10))
        
        use_shifted_cb = ttk.Checkbutton(sample_frame, text="Use Shifted Sample Points", 
                                         variable=use_shifted_points_var, command=update_ui_state)
        use_shifted_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(sample_frame, text="Shift Value (px):").grid(row=1, column=0, sticky=tk.W, pady=2)
        shift_value_entry = ttk.Spinbox(sample_frame, from_=1, to=20, textvariable=shift_value_var, width=5)
        shift_value_entry.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Window sizes section
        window_frame = ttk.LabelFrame(main_frame, text="Window Sizes", padding="10 10 10 10")
        window_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Window 1
        use_window1_cb = ttk.Checkbutton(window_frame, text="Window 1", 
                                        variable=use_window1_var, command=update_ui_state)
        use_window1_cb.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(window_frame, text="Size:").grid(row=0, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        window1_size_entry = ttk.Spinbox(window_frame, from_=5, to=51, increment=2, 
                                        textvariable=window1_size_var, width=5)
        window1_size_entry.grid(row=0, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        
        # Window 2
        use_window2_cb = ttk.Checkbutton(window_frame, text="Window 2", 
                                        variable=use_window2_var, command=update_ui_state)
        use_window2_cb.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(window_frame, text="Size:").grid(row=1, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        window2_size_entry = ttk.Spinbox(window_frame, from_=5, to=51, increment=2, 
                                        textvariable=window2_size_var, width=5)
        window2_size_entry.grid(row=1, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        
        # Window 3
        use_window3_cb = ttk.Checkbutton(window_frame, text="Window 3", 
                                        variable=use_window3_var, command=update_ui_state)
        use_window3_cb.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(window_frame, text="Size:").grid(row=2, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        window3_size_entry = ttk.Spinbox(window_frame, from_=5, to=51, increment=2, 
                                        textvariable=window3_size_var, width=5)
        window3_size_entry.grid(row=2, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        
        # Filtering method section
        filter_frame = ttk.LabelFrame(main_frame, text="Filtering Method", padding="10 10 10 10")
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(filter_frame, text="Average", variable=filter_method_var, 
                       value="average").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(filter_frame, text="Consensus", variable=filter_method_var, 
                       value="consensus").pack(anchor=tk.W, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def on_cancel():
            dialog.destroy()
        
        def on_ok():
            # Validate window sizes are odd numbers
            for var in [window1_size_var, window2_size_var, window3_size_var]:
                if var.get() % 2 == 0:
                    messagebox.showerror("Error", "Window sizes must be odd numbers")
                    return
            
            # Save tracking settings
            self.current_project.setdefault('tracking_settings', {}).update({
                'use_shifted_points': use_shifted_points_var.get(),
                'shift_value': shift_value_var.get(),
                'use_window1': use_window1_var.get(),
                'window1_size': window1_size_var.get(),
                'use_window2': use_window2_var.get(),
                'window2_size': window2_size_var.get(),
                'use_window3': use_window3_var.get(),
                'window3_size': window3_size_var.get(),
                'filter_method': filter_method_var.get()
            })
            
            # Collect configuration
            result["cancelled"] = False
            result["use_shifted_points"] = use_shifted_points_var.get()
            result["shift_value"] = shift_value_var.get()
            
            result["windows"] = []
            if use_window1_var.get():
                result["windows"].append(window1_size_var.get())
            if use_window2_var.get():
                result["windows"].append(window2_size_var.get())
            if use_window3_var.get():
                result["windows"].append(window3_size_var.get())
            
            result["filter_method"] = filter_method_var.get()
            
            dialog.destroy()
        
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.RIGHT)
        
        # Initialize UI state
        update_ui_state()
        
        # Center the dialog on the screen
        self.center_window(dialog)
        
        # Wait for dialog to close
        dialog.wait_window()
        
        return None if result["cancelled"] else result
    
    def track_points_with_config(self, video_path, initial_points, config):
        """Track points using the configured parameters"""
        from app.tracking import track_points_with_consensus
        
        # If no windows specified, use default
        if not config["windows"]:
            config["windows"] = [21]
        
        # Call the tracking function with the configured parameters
        return track_points_with_consensus(
            video_path, 
            initial_points, 
            use_shifted_points=config["use_shifted_points"],
            shift_value=config["shift_value"],
            window_sizes=config["windows"],
            filter_method=config["filter_method"]
        )
    
    def center_window(self, window):
        """Center a window on the screen"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}') 