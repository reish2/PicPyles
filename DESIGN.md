# Design Document: PicPyles

**Document Version**: 1.1  
**Author**: Reish2  
**Date**: 12.8.24

## Project Overview

PicPyles is a Python-based application designed to provide a robust solution for viewing and organizing large collections of images stored locally. The application allows users to sort images into thematic piles, zoom in/out for detailed or overview visualizations, and manage images with a minimal, intuitive interface.

## Objectives

- **High Performance**: Efficiently handle and render large, high-resolution images.
- **User Privacy**: Operate entirely locally, with no data sent externally.
- **Ease of Use**: Simple, intuitive UI for managing and viewing images.
- **Scalability**: Capable of handling potentially thousands of 20MP images.

## Technical Requirements

- **Language**: Python 3.9+
- **GUI Framework**:
  - **PyQt5**: A popular and well-maintained GUI framework for Python, offering a comprehensive set of tools for building desktop applications.

- **Graphics Library**:
  - **PyOpenGL**: A Python binding to the OpenGL API, suitable for 2D and 3D rendering.

- **Image Handling Library**:
  - **Pillow**: A friendly fork of the Python Imaging Library (PIL), providing an easy-to-use interface for image processing and manipulation.

## System Architecture

- **Image Canvas**: Central component for displaying images. Will support interactive features like zooming and panning.
- **Image Management**: Logic for loading, resizing, and organizing images into a dictionary-like structure for quick access and manipulation.
- **UI Components**: Minimal set of interactive elements for user input, including tools for sorting and navigating images.

## Components

1. **Canvas Renderer**
   - **Purpose**: Handle all drawing operations, including rendering thumbnails and full images on a 2D canvas.
   - **Technology**: PyOpenGL for GPU-accelerated graphics processing.

2. **Image Loader**
   - **Purpose**: Efficiently load and decode images, generating thumbnails and storing these for quick access.
   - **Technology**: Pillow.

3. **UI Controller**
   - **Purpose**: Manage user interactions, translating them into actions performed by the application (e.g., zooming, piling images).
   - **Technology**: PyQt5.

4. **File System Interface**
   - **Purpose**: Interface with the local file system to load images from user-selected directories.
   - **Technology**: Python's standard library (os, pathlib).

## User Flows

- **Loading Images**: User selects a directory; app scans the directory and loads images into the application.
- **Viewing and Organizing Images**: User interacts with the canvas to sort images into piles, zoom in/out, and focus on specific images.
- **Detailed Image View**: Clicking on a thumbnail initiates a smooth zoom transition to view the image in detail.

## Future Considerations

- **Extensibility**: How can we extend the app’s capabilities in the future (e.g., adding image editing features)?
- **Performance Optimization**: Strategies for further optimization, particularly in memory management and rendering.
- **Motion Photos**: have a representative thumbnail of the MPhoto with a playable icon on it. When opened or zoomed in it loops.
- **Videos**: have a representative thumbnail of the video with a playable icon on it. When opened or zoomed in it plays.

## Challenges and Risks

- **Performance**: Ensuring the application remains responsive and efficient while handling large image files.
- **UI Design**: Creating a user-friendly interface with minimal design that still offers all required functionalities.