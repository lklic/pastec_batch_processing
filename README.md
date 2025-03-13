# Pastec Batch Processing

This repository contains Python scripts for batch processing images with the [Pastec](https://github.com/Visu4link/pastec) image recognition engine. These scripts allow you to:

1. **Add images to the Pastec index in batches** (`pastec-batch-index-add.py`)
2. **Search for similar images in the Pastec index** (`pastec-batch-index-search.py`)

## Prerequisites

- Python 3.6 or higher
- Required Python packages: `aiohttp`, `asyncio`
- A running Pastec server (default: http://localhost:4212)
- A CSV file containing image information
- Image files organized in a folder structure

## Quick Start

1. Prepare your CSV file with image information (see `images.csv` for an example)
2. Update the `BASE_PATH` constant in the scripts to point to your image directory
3. Run the indexing script to add images to the Pastec index:
   ```bash
   python pastec-batch-index-add.py
   ```
4. Run the search script to find similar images:
   ```bash
   python pastec-batch-index-search.py
   ```

## Documentation

- For detailed information about the indexing script, see [pastec-batch-add-README.md](pastec-batch-add-README.md)
- For detailed information about the search script, see [pastec-batch-search-README.md](pastec-batch-search-README.md)

## Typical Workflow

1. Index your images using `pastec-batch-index-add.py`
2. Search for similar images using `pastec-batch-index-search.py`
3. Analyze the results in the generated CSV files

## Command-line Options

Both scripts support the following command-line options:

```bash
# Run in test mode (process only the first 100 images)
python script.py --testing

# Specify a different CSV file
python script.py --csv my_images.csv

# Specify a different base path
python script.py --base-path /path/to/my/images
```

## Output Files

- The indexing script generates output files in the `Add_log` directory
- The search script generates output files in the `Search_log` directory
