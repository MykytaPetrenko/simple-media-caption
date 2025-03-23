#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Media Captioning Tool - Project Manager
"""

import os
import json
import shutil
from tkinter import messagebox

class ProjectManager:
    def __init__(self, app):
        self.app = app
    
    def load_project(self, file_path):
        """Load a project from a JSON file"""
        try:
            with open(file_path, 'r') as f:
                project_data = json.load(f)
            
            # Validate project data
            if not isinstance(project_data, dict) or 'media_path' not in project_data:
                raise ValueError("Invalid project file format")
            
            # Check if media path exists
            if not os.path.isdir(project_data['media_path']):
                messagebox.showwarning(
                    "Media Path Not Found",
                    f"The media path '{project_data['media_path']}' does not exist. "
                    "Please update the media path after loading."
                )
            
            # Check if masks path exists, create if needed
            masks_path = project_data.get('masks_path')
            if not masks_path or not os.path.isdir(masks_path):
                # Default masks directory is sibling to media directory
                project_dir = os.path.dirname(file_path)
                masks_path = os.path.join(project_dir, "masks")
                os.makedirs(masks_path, exist_ok=True)
                project_data['masks_path'] = masks_path
            
            # Check if captions path exists, create if needed
            captions_path = project_data.get('captions_path')
            if not captions_path or not os.path.isdir(captions_path):
                # Default captions directory is sibling to media directory
                project_dir = os.path.dirname(file_path)
                captions_path = os.path.join(project_dir, "captions")
                os.makedirs(captions_path, exist_ok=True)
                project_data['captions_path'] = captions_path
            
            # Set file path in project data
            project_data['file_path'] = file_path
            
            # Update application state
            self.app.current_project = project_data
            self.app.current_media = None
            self.app.update_ui_state()
            
            messagebox.showinfo("Success", f"Project loaded from {file_path}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project: {str(e)}")
    
    def save_project(self, file_path):
        """Save the current project to a JSON file"""
        if not self.app.current_project:
            return
        
        try:
            # Create a copy of the project data without the file_path
            project_data = self.app.current_project.copy()
            if 'file_path' in project_data:
                del project_data['file_path']
            
            # Save current caption if there's a current media
            if self.app.current_media:
                media_id = self.app.current_media['id']
                caption = self.app.caption_text.get(1.0, "end-1c")
                project_data['media_files'][media_id]['caption'] = caption
                
                # Save current mask
                if hasattr(self.app, 'mask_editor'):
                    self.app.mask_editor.save_mask()
            
            with open(file_path, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            # Update file path in current project
            self.app.current_project['file_path'] = file_path
            
            messagebox.showinfo("Success", f"Project saved to {file_path}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project: {str(e)}")
    
    def export_dataset(self, export_dir):
        """Export the project as a dataset"""
        if not self.app.current_project:
            return
        
        try:
            # Create export directory if it doesn't exist
            os.makedirs(export_dir, exist_ok=True)
            
            # Get media files with captions
            media_files = self.app.current_project.get('media_files', {})
            media_path = self.app.current_project.get('media_path', '')
            masks_path = self.app.current_project.get('masks_path', '')
            
            if not media_path or not os.path.isdir(media_path):
                raise ValueError("Invalid media path")
            
            # Copy media files, masks and create caption files
            copied_count = 0
            for media_id, media_data in media_files.items():
                # Copy media file
                source_path = os.path.join(media_path, media_id)
                if not os.path.isfile(source_path):
                    continue
                
                dest_path = os.path.join(export_dir, media_id)
                shutil.copy2(source_path, dest_path)
                
                # Create caption file
                caption = media_data.get('caption', '')
                caption_file = os.path.splitext(dest_path)[0] + '.txt'
                with open(caption_file, 'w') as f:
                    f.write(caption)
                
                # Copy mask file if it exists
                name, _ = os.path.splitext(media_id)
                mask_file = name + '.png'
                mask_source = os.path.join(masks_path, mask_file)
                if os.path.isfile(mask_source):
                    mask_dest = os.path.join(export_dir, mask_file)
                    shutil.copy2(mask_source, mask_dest)
                
                copied_count += 1
            
            messagebox.showinfo(
                "Export Complete",
                f"Exported {copied_count} media files with captions and masks to {export_dir}"
            )
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export dataset: {str(e)}") 