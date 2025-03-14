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
            
            if not media_path or not os.path.isdir(media_path):
                raise ValueError("Invalid media path")
            
            # Copy media files and create caption files
            copied_count = 0
            for media_id, media_data in media_files.items():
                source_path = os.path.join(media_path, media_id)
                if not os.path.isfile(source_path):
                    continue
                
                # Copy media file
                dest_path = os.path.join(export_dir, media_id)
                shutil.copy2(source_path, dest_path)
                
                # Create caption file
                caption = media_data.get('caption', '')
                caption_file = os.path.splitext(dest_path)[0] + '.txt'
                with open(caption_file, 'w') as f:
                    f.write(caption)
                
                copied_count += 1
            
            messagebox.showinfo(
                "Export Complete",
                f"Exported {copied_count} media files with captions to {export_dir}"
            )
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export dataset: {str(e)}") 