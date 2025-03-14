#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Media Captioning Tool - Main Application Entry Point
"""

import tkinter as tk
from app.application import MediaCaptioningApp

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Media Captioning Tool")
    root.geometry("1200x800")
    
    app = MediaCaptioningApp(root)
    
    # Create a new project by default
    app.new_project()
    
    root.mainloop()