# How to Start the AI Multimedia Recommendation System

## Quick Start

### Option 1: Use the startup script

```bash
cd /Users/macbook/Desktop/AI-Pedia/Project
./start.sh
```

The startup script will automatically:
- Check the Python environment
- Check and install dependencies
- Create required directories
- Start the application

### Option 2: Start manually

```bash
# 1. Go to project directory
cd /Users/macbook/Desktop/AI-Pedia/Project

# 2. Install dependencies (required on first run)
pip3 install -r requirements.txt

# 3. Start the app
python3 app.py
```

## After startup

If the app starts successfully, you will see output similar to:

```
==================================================
AI Multimedia Recommendation System
==================================================
Uploads dir : /Users/macbook/Desktop/AI-Pedia/Project/data/uploads
Results dir : /Users/macbook/Desktop/AI-Pedia/Project/data/results
Outputs dir : /Users/macbook/Desktop/AI-Pedia/Project/data/outputs
==================================================
Visit: http://localhost:5000
Press Ctrl+C to stop server
==================================================
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

## Accessing the app

Open your browser and visit:
- **http://localhost:5000**
- or **http://127.0.0.1:5000**

## Stopping the app

In the terminal where the app is running, press:

```bash
Ctrl + C
```

## Common issues

### 1. Port already in use

If port 5000 is occupied, modify the last line in `app.py`:

```python
app.run(debug=True, port=5001)  # change to another port
```

### 2. Missing dependencies

If you see errors like `ModuleNotFoundError`, run:

```bash
pip3 install -r requirements.txt
```

### 3. Permission issues

If the startup script cannot be executed, run:

```bash
chmod +x start.sh
```

## Usage flow

1. **Start the app** → run `python3 app.py` or `./start.sh`  
2. **Open browser** → visit `http://localhost:5000`  
3. **Upload files** → upload a ZIP containing **at least 10** AI/ML‑related TXT/PDF documents  
4. **Wait for processing** → the system will extract AI‑related keywords and search AI domain resources  
5. **Download results** → download the recommendation ZIP (irrelevant content and contact info already filtered)

## Notes

- **Document topic**: recommended to upload AI/Machine Learning related documents (e.g. ML, DL, neural networks, etc.)
- **File formats**: TXT and PDF are supported (PDF will be automatically converted to TXT)
- **File count**: the uploaded ZIP must contain **at least 10** TXT/PDF documents
- **Network**: a stable network connection is required (for accessing external resources)
- **Processing time**: depends on document count and network speed (typically 2–5 minutes)
- **Recommended content**: the system automatically filters non‑AI content (e.g. policy reports, building issues, etc.)

