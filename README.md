# SteelSpanPy

Python library that automatically creates steel industrial building models (hangar, factory, etc.) using the ETABS API.

## What It Does

- Automatically creates columns, beams, vertical braces and roof braces
- Defines earthquake loads and response spectra according to TBDY 2018
- Automatically sets up load combinations (1.4G, 1.2G+1.6S, etc.)
- AI-powered chatbot for defining geometry and section parameters in natural language

## Requirements

- Python 3.x
- ETABS (CSI) must be installed
- numpy
- comtypes

## Usage

```bash
python steelspanpy/main.py
```

The program asks for a filename, then opens ETABS and automatically builds the model.

## Modules

| Module | Description |
|--------|-------------|
| config.py | Geometry, load, section and seismic parameters |
| geometry.py | Point generation and roof geometry |
| sections.py | Section and material definitions |
| loads.py | Load patterns and combinations |
| seismic.py | TBDY 2018 seismic calculations |
| elements.py | Column, beam and brace creation |
| etabs_connect.py | ETABS connection and file management |
| main.py | Main workflow |

## Roadmap

- [x] Modular structure
- [ ] AI chatbot integration
- [ ] GUI interface
