#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Media Captioning Tool - Mask Manager
"""

import tkinter as tk

class MaskManager:
    def __init__(self, app, canvas):
        self.app = app
        self.canvas = canvas
        self.active_tool = None
        self.current_mask = None
        self.current_points = []
        self.original_points = []  # Store original points for cancel operation
        self.current_polygon = None
        self.point_markers = []
        self.selected_point_index = -1
        self.editing_mask_id = None  # Store the ID of the mask being edited
        self.current_frame = 0  # Current frame for interpolation
        
        # Default style settings
        self.fill_color = "red"
        self.fill_opacity = 0.3
        self.outline_color = "yellow"
        self.outline_width = 2
        self.show_fill = True
        self.show_outline = True
        
        # Bind canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Escape>", self.cancel_current_operation)
    
    def activate_create_mask_tool(self):
        """Activate the create mask tool"""
        self.active_tool = "create"
        self.current_points = []
        self.current_polygon = None
        self.editing_mask_id = None
        self.clear_point_markers()
        self.canvas.config(cursor="crosshair")
    
    def activate_keyframe_mask_tool(self, mask):
        """Activate the keyframe mask tool for the given mask"""
        self.active_tool = "keyframe"
        self.current_mask = mask
        self.current_points = self.get_interpolated_points(mask, self.current_frame)
        self.original_points = self.current_points.copy()  # Store original points
        self.current_polygon = None
        self.editing_mask_id = mask['id']  # Store the ID of the mask being edited
        self.clear_point_markers()
        self.draw_mask_points()
        self.canvas.config(cursor="hand2")
        
        # Redraw all masks to hide the one being edited
        self.draw_all_masks()
    
    def deactivate_tools(self):
        """Deactivate all tools"""
        self.active_tool = None
        self.current_mask = None
        self.current_points = []
        self.original_points = []
        self.current_polygon = None
        self.editing_mask_id = None
        self.clear_point_markers()
        self.canvas.config(cursor="")
    
    def apply_keyframe(self):
        """Apply the current edit as a new keyframe"""
        if self.active_tool == "keyframe" and self.current_mask:
            # Get the current frame number from the video
            current_frame = self.app.media_viewer.current_frame_index
            
            # Store the mask ID before clearing state
            mask_id = self.current_mask['id']
            
            # Add the keyframe at the current frame
            self.app.add_keyframe(mask_id, self.current_points, current_frame)
            
            # Clear editing state
            self.deactivate_tools()
            
            # Redraw all masks with interpolated positions
            self.draw_all_masks()
    
    def on_canvas_click(self, event):
        """Handle canvas click event"""
        if not self.active_tool:
            return
        
        # Convert canvas coordinates to media coordinates
        canvas_x, canvas_y = event.x, event.y
        x, y = self.app.media_viewer.canvas_to_media_coords(canvas_x, canvas_y)
        
        if self.active_tool == "create":
            # Creating a new mask
            if not self.current_points:
                # First point
                self.current_points.append((x, y))
                self.draw_point(x, y)
            else:
                # Check if clicking near the first point to close the polygon
                first_x, first_y = self.current_points[0]
                # Convert to canvas coordinates for distance check
                first_canvas_x, first_canvas_y = self.app.media_viewer.media_to_canvas_coords(first_x, first_y)
                if len(self.current_points) > 2 and self.is_near_point(canvas_x, canvas_y, first_canvas_x, first_canvas_y):
                    # Close the polygon
                    self.finish_create_mask()
                else:
                    # Add a new point
                    self.current_points.append((x, y))
                    self.draw_point(x, y)
                    self.update_polygon()
        
        elif self.active_tool in ["edit", "keyframe"]:
            # Editing an existing mask or keyframe
            # Check if clicking on a point
            for i, (px, py) in enumerate(self.current_points):
                # Convert to canvas coordinates for distance check
                canvas_px, canvas_py = self.app.media_viewer.media_to_canvas_coords(px, py)
                if self.is_near_point(canvas_x, canvas_y, canvas_px, canvas_py):
                    self.selected_point_index = i
                    break
    
    def on_canvas_motion(self, event):
        """Handle canvas motion event"""
        if not self.active_tool or self.active_tool != "create" or not self.current_points:
            return
        
        # Update temporary line when creating a mask
        canvas_x, canvas_y = event.x, event.y
        
        # Remove previous temporary line
        self.canvas.delete("temp_line")
        
        # Draw temporary line from last point to current position
        last_x, last_y = self.current_points[-1]
        # Convert media coordinates to canvas coordinates
        last_canvas_x, last_canvas_y = self.app.media_viewer.media_to_canvas_coords(last_x, last_y)
        
        self.canvas.create_line(
            last_canvas_x, last_canvas_y, canvas_x, canvas_y,
            fill=self.outline_color,
            width=self.outline_width,
            tags="temp_line"
        )
    
    def on_canvas_drag(self, event):
        """Handle canvas drag event"""
        if not self.active_tool or (self.active_tool not in ["edit", "keyframe"]) or self.selected_point_index < 0:
            return
        
        # Convert canvas coordinates to media coordinates
        canvas_x, canvas_y = event.x, event.y
        x, y = self.app.media_viewer.canvas_to_media_coords(canvas_x, canvas_y)
        
        # Move the selected point
        self.current_points[self.selected_point_index] = (x, y)
        
        # Update the display
        self.update_point_markers()
        self.update_polygon()
    
    def on_canvas_release(self, event):
        """Handle canvas release event"""
        if not self.active_tool or (self.active_tool not in ["edit", "keyframe"]) or self.selected_point_index < 0:
            return
        
        # Reset selected point index
        self.selected_point_index = -1
    
    def cancel_current_operation(self, event=None):
        """Cancel the current operation"""
        if self.active_tool == "create":
            self.deactivate_tools()
        elif self.active_tool in ["edit", "keyframe"]:
            # Restore original points
            if self.current_mask:
                self.current_points = self.original_points.copy()
                self.update_point_markers()
                self.update_polygon()
                self.deactivate_tools()
                
                # Redraw all masks
                self.draw_all_masks()
    
    def finish_create_mask(self):
        """Finish creating a mask"""
        if not self.current_points or len(self.current_points) < 3:
            return
        
        # Add the mask to the project
        new_mask = self.app.add_mask(self.current_points)
        
        # Clear current state
        self.current_points = []
        self.clear_point_markers()
        self.canvas.delete("temp_line")
        self.canvas.delete("current_polygon")
        
        # Deactivate tools
        self.deactivate_tools()
        
        # Redraw all masks
        self.draw_all_masks()
    
    def draw_mask_points(self):
        """Draw the points of the current mask"""
        self.clear_point_markers()
        
        for x, y in self.current_points:
            self.draw_point(x, y)
        
        self.update_polygon()
    
    def draw_point(self, x, y):
        """Draw a point marker at the given coordinates"""
        # Convert media coordinates to canvas coordinates
        canvas_x, canvas_y = self.app.media_viewer.media_to_canvas_coords(x, y)
        
        point_radius = 5
        marker = self.canvas.create_oval(
            canvas_x - point_radius, canvas_y - point_radius,
            canvas_x + point_radius, canvas_y + point_radius,
            fill="white",
            outline="black",
            tags="point_marker"
        )
        self.point_markers.append(marker)
    
    def update_point_markers(self):
        """Update the position of point markers"""
        point_radius = 5
        
        for i, (x, y) in enumerate(self.current_points):
            # Convert media coordinates to canvas coordinates
            canvas_x, canvas_y = self.app.media_viewer.media_to_canvas_coords(x, y)
            
            if i < len(self.point_markers):
                self.canvas.coords(
                    self.point_markers[i],
                    canvas_x - point_radius, canvas_y - point_radius,
                    canvas_x + point_radius, canvas_y + point_radius
                )
    
    def clear_point_markers(self):
        """Clear all point markers"""
        self.canvas.delete("point_marker")
        self.point_markers = []
    
    def update_polygon(self):
        """Update the polygon display"""
        if not self.current_points or len(self.current_points) < 2:
            return
        
        # Delete previous polygon
        self.canvas.delete("current_polygon")
        
        # Create new polygon
        if len(self.current_points) >= 3:
            # Convert media coordinates to canvas coordinates and flatten
            flat_points = []
            for x, y in self.current_points:
                canvas_x, canvas_y = self.app.media_viewer.media_to_canvas_coords(x, y)
                flat_points.extend([canvas_x, canvas_y])
            
            # Create the polygon
            fill = self.fill_color if self.show_fill else ""
            outline = self.outline_color if self.show_outline else ""
            
            # Apply opacity using stipple pattern
            stipple = ""
            if self.show_fill and self.fill_opacity < 1.0:
                if self.fill_opacity < 0.25:
                    stipple = "gray12"
                elif self.fill_opacity < 0.5:
                    stipple = "gray25"
                elif self.fill_opacity < 0.75:
                    stipple = "gray50"
                else:
                    stipple = "gray75"
            
            self.current_polygon = self.canvas.create_polygon(
                flat_points,
                fill=fill,
                outline=outline,
                width=self.outline_width,
                tags="current_polygon",
                stipple=stipple
            )
        else:
            # Just draw a line for two points
            x1, y1 = self.current_points[0]
            x2, y2 = self.current_points[1]
            # Convert media coordinates to canvas coordinates
            canvas_x1, canvas_y1 = self.app.media_viewer.media_to_canvas_coords(x1, y1)
            canvas_x2, canvas_y2 = self.app.media_viewer.media_to_canvas_coords(x2, y2)
            
            self.canvas.create_line(
                canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                fill=self.outline_color,
                width=self.outline_width,
                tags="current_polygon"
            )
    
    def is_near_point(self, x, y, px, py, threshold=10):
        """Check if (x, y) is near the point (px, py)"""
        return abs(x - px) <= threshold and abs(y - py) <= threshold
    
    def set_fill_color(self, color):
        """Set the fill color for masks"""
        self.fill_color = color
        self.update_polygon()
    
    def set_fill_opacity(self, opacity):
        """Set the fill opacity for masks"""
        self.fill_opacity = float(opacity)
        self.update_polygon()
    
    def set_outline_color(self, color):
        """Set the outline color for masks"""
        self.outline_color = color
        self.update_polygon()
    
    def set_outline_width(self, width):
        """Set the outline width for masks"""
        self.outline_width = int(width)
        self.update_polygon()
    
    def toggle_fill(self, show):
        """Toggle whether to show the fill"""
        self.show_fill = bool(show)
        self.update_polygon()
    
    def toggle_outline(self, show):
        """Toggle whether to show the outline"""
        self.show_outline = bool(show)
        self.update_polygon()
    
    def get_interpolated_points(self, mask, frame):
        """Get interpolated points for the given frame"""
        if not mask['keyframes']:
            return []
        
        # Find the keyframes to interpolate between
        prev_keyframe = None
        next_keyframe = None
        
        for i, keyframe in enumerate(mask['keyframes']):
            if keyframe['frame'] <= frame:
                prev_keyframe = keyframe
            else:
                next_keyframe = keyframe
                break
        
        # If we're before the first keyframe or after the last keyframe
        if not prev_keyframe:
            return mask['keyframes'][0]['points'].copy()
        if not next_keyframe:
            return mask['keyframes'][-1]['points'].copy()
        
        # Calculate interpolation factor
        total_frames = next_keyframe['frame'] - prev_keyframe['frame']
        if total_frames == 0:
            return prev_keyframe['points']
        
        factor = (frame - prev_keyframe['frame']) / total_frames
        
        # Interpolate between points
        interpolated_points = []
        for prev_point, next_point in zip(prev_keyframe['points'], next_keyframe['points']):
            x = prev_point[0] + (next_point[0] - prev_point[0]) * factor
            y = prev_point[1] + (next_point[1] - prev_point[1]) * factor
            interpolated_points.append((x, y))
        
        return interpolated_points
    
    def update_frame(self, frame):
        """Update the current frame for interpolation"""
        self.current_frame = frame
        if self.current_mask:
            # Update points based on interpolation
            self.current_points = self.get_interpolated_points(self.current_mask, frame)
            self.update_point_markers()
            self.update_polygon()
    
    def draw_all_masks(self):
        """Draw all masks for the current media"""
        if not self.app.current_media:
            return
        
        # Clear existing masks
        self.canvas.delete("mask")
        
        # Get masks for current media
        media_id = self.app.current_media['id']
        masks = self.app.current_project.get('masks', {}).get(media_id, [])
        
        for mask in masks:
            # Skip the mask being edited
            if self.editing_mask_id and mask['id'] == self.editing_mask_id:
                continue
            
            # Get interpolated points for current frame
            points = self.get_interpolated_points(mask, self.current_frame)
            if len(points) < 3:
                continue
            
            # Convert media coordinates to canvas coordinates and flatten
            flat_points = []
            for x, y in points:
                canvas_x, canvas_y = self.app.media_viewer.media_to_canvas_coords(x, y)
                flat_points.extend([canvas_x, canvas_y])
            
            # Create the polygon
            fill = self.fill_color if self.show_fill else ""
            outline = self.outline_color if self.show_outline else ""
            
            # Apply opacity using stipple pattern
            stipple = ""
            if self.show_fill and self.fill_opacity < 1.0:
                if self.fill_opacity < 0.25:
                    stipple = "gray12"
                elif self.fill_opacity < 0.5:
                    stipple = "gray25"
                elif self.fill_opacity < 0.75:
                    stipple = "gray50"
                else:
                    stipple = "gray75"
            
            self.canvas.create_polygon(
                flat_points,
                fill=fill,
                outline=outline,
                width=self.outline_width,
                tags=("mask", f"mask_{mask['id']}"),
                stipple=stipple
            )
        
        # If we're editing a mask, redraw the editing polygon
        if self.active_tool in ["edit", "keyframe"] and self.current_points:
            self.update_polygon() 