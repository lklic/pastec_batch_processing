# Pastec Batch Image Indexing

This document explains how to use the `pastec-batch-index-add.py` script to add images to the Pastec index in batches.

## Overview

The script allows you to add a large number of images to the Pastec index by processing them in batches. It reads image information from a CSV file, constructs file paths based on a base path and folder structure, and sends the images to the Pastec API for indexing.

Key features:
- Process images in configurable batch sizes (default: 100 images per batch)
- Save the index at configurable intervals (default: every 1000 images)
- Detailed logging of the indexing process
- Tracking of missing files
- CSV output of indexing results

## Prerequisites

- Python 3.6 or higher
- Required Python packages: `aiohttp`, `asyncio`
- A running Pastec server (default: http://localhost:4212)
- A CSV file containing image information
- Image files organized in a folder structure

## CSV Format

The script expects a CSV file with at least the following columns:
- An ID column (default: "ID"): Unique identifier for each image
- A filename column (default: "Filename"): Name of the image file
- A folder column (default: "Folder"): Subfolder where the image is located

Example CSV format:

```
ID,Filename,Folder,Description
1001,image1.jpg,folder1,Sample image 1
1002,image2.jpg,folder1,Sample image 2
1003,image3.jpg,folder2,Sample image 3
```

You can customize the column names by modifying the constants at the top of the script:
```python
ID_COLUMN = "ID"  # Column containing the image ID
FILENAME_COLUMN = "Filename"  # Column containing the filename
FOLDER_COLUMN = "Folder"  # Column containing the folder name
```

## File Structure

The script expects images to be organized in a folder structure like this:

```
/base/path/
  ├── folder1/
  │   ├── image1.jpg
  │   └── image2.jpg
  ├── folder2/
  │   ├── image3.jpg
  │   └── image4.jpg
  └── ...
```

The full path to each image is constructed as: `BASE_PATH/folder/filename`

## Configuration

You can configure the script by modifying the constants at the top of the file:

```python
API_URL = "http://localhost:4212/index/images/"  # Pastec API endpoint for adding images
SAVE_INDEX_URL = "http://localhost:4212/index/io"  # Pastec API endpoint for saving the index
SOURCE_CSV = "images.csv"  # Default CSV filename
ADD_LOG_DIR = "Add_log"  # Directory for add logs
LOG_FILE = os.path.join(ADD_LOG_DIR, "pastec_batch_index_add_log.txt")  # Log file for general messages
MISSING_FILES_LOG = os.path.join(ADD_LOG_DIR, "pastec_batch_index_add_missing_files_log.txt")  # Log file for missing files
RESULTS_CSV = os.path.join(ADD_LOG_DIR, "pastec_batch_index_add_log_results.csv")  # CSV file for indexing results
BASE_PATH = "/path/to/images"  # Base path where images are stored
BATCH_SIZE = 100  # Number of images to process in each batch
SAVE_INTERVAL = 1000  # Save index after processing this many images
INDEX_PATH = "/pastec/build/pastec-index/pastec_index.dat"  # Path to save the index
```

## Running the Script

Basic usage:

```bash
python pastec-batch-index-add.py
```

With command-line options:

```bash
# Run in test mode (process only the first 100 images)
python pastec-batch-index-add.py --testing

# Specify a different CSV file
python pastec-batch-index-add.py --csv my_images.csv

# Specify a different base path
python pastec-batch-index-add.py --base-path /path/to/my/images

# Combine options
python pastec-batch-index-add.py --testing --csv my_images.csv --base-path /path/to/my/images
```

## Output Files

The script generates several output files in the `Add_log` directory:

1. **Log file** (`pastec_batch_index_add_log.txt`): Contains detailed information about the indexing process, including batch processing, API responses, and index saving.

2. **Missing files log** (`pastec_batch_index_add_missing_files_log.txt`): Lists files that could not be found at the expected path.

3. **Results CSV** (`pastec_batch_index_add_log_results.csv`): Contains the results of the indexing process for each image, including:
   - ID: Image ID
   - filename: Image filename
   - status: SUCCESS or ERROR
   - response: API response or error message
   - timestamp: When the image was processed

## Troubleshooting

### Common Issues

1. **File not found errors**: Check that your BASE_PATH and folder structure match what's in your CSV file. Make sure the filenames in the CSV match the actual filenames on disk.

2. **API connection errors**: Ensure that the Pastec server is running and accessible at the URL specified in API_URL.

3. **CSV parsing errors**: Verify that your CSV file has the expected column names and format. Check for any special characters or encoding issues.

### Performance Tips

- The default batch size (100) is optimized for performance, but you can adjust it based on your system's capabilities.
- If you're processing a very large number of images, consider increasing the SAVE_INTERVAL to reduce the frequency of index saves.
- For very large datasets, consider splitting your CSV file into smaller chunks and processing them separately.

## Example

1. Prepare your CSV file with image information:
   ```
   ID,Filename,Folder
   1001,image1.jpg,folder1
   1002,image2.jpg,folder1
   ```

2. Update the BASE_PATH constant in the script to point to your image directory.

3. Run the script:
   ```bash
   python pastec-batch-index-add.py
   ```

4. Check the `Add_log` directory for the log file and results CSV to monitor progress and indexing status.
