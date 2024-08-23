# PicPyles

A Python-based application for viewing and organizing large collections of images stored locally.

## Getting Started

To get started with PicPyles, clone the repository, set up a virtual environment, install dependencies, and run the application:

```bash
git clone https://github.com/reish2/PicPyles.git
cd PicPyles
python -m venv picpyles-env
source picpyles-env/bin/activate  # On Linux/Mac
# or
picpyles-env\Scripts\activate  # On Windows
pip install -r requirements.txt
python main.py
```

## Requirements

* Python 3.9+
* PyQt5
* PyOpenGL
* Pillow
* Numpy

## Project Structure

The project is organized into the following directories:

- `views/`: GUI-related code.
- `models/`: Data structures and logic.
- `controllers/`: Handles interactions between models and views.
- `assets/`: Icons and fonts.
- `requirements.txt`: Lists dependencies.
- `main.py`: Application entry point.

## Contributing

Contributions are welcome! If you'd like to contribute to the project, please fork the repository and submit a pull request.

## License

See the LICENSE file for details.