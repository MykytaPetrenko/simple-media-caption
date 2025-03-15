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
        export_menu.add_command(label="Export Dataset", command=self.export_dataset)
        export_menu.add_command(label="Export Masks", command=self.export_masks)
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
    
    def export_dataset(self):
        """Export the project as a dataset"""
        if not self.current_project:
            messagebox.showerror("Error", "No project is currently open")
            return
        
        export_dir = filedialog.askdirectory(title="Select Export Directory")
        if export_dir:
            self.project_manager.export_dataset(export_dir)
    
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
        
        # Update UI
        self.master.update()
        
        try:
            # Track points across frames
            tracked_points = track_points_with_lk_and_kalman(media_path, initial_points)
            
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
    
    def export_masks(self):
        """Export masks as black and white images/videos"""
        if not self.current_project:
            messagebox.showerror("Error", "No project is currently open")
            return
        
        export_dir = filedialog.askdirectory(title="Select Export Directory for Masks")
        if not export_dir:
            return
            
        import cv2
        import numpy as np
        from PIL import Image, ImageDraw
        
        # Create export directory if it doesn't exist
        os.makedirs(export_dir, exist_ok=True)
        
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
                mask_path = os.path.join(export_dir, f"{os.path.splitext(media_id)[0]}_mask.mp4")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(mask_path, fourcc, fps, (width, height), False)
                
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
                        if points:
                            # Convert points to numpy array
                            points = np.array(points, dtype=np.int32)
                            # Fill the polygon with white (255)
                            cv2.fillPoly(mask_frame, [points], 255)
                    
                    # Write the mask frame
                    out.write(mask_frame)
                    frame_idx += 1
                
                # Release video resources
                cap.release()
                out.release()
                
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
                    if points:
                        # Convert points to flat list for PIL
                        flat_points = [coord for point in points for coord in point]
                        # Fill the polygon with white (255)
                        draw.polygon(flat_points, fill=255)
                
                # Save the mask image
                mask_path = os.path.join(export_dir, f"{os.path.splitext(media_id)[0]}_mask{os.path.splitext(media_id)[1]}")
                mask_img.save(mask_path)
        
        messagebox.showinfo("Success", "Masks exported successfully!") 