# Pastec Batch Image Search

This document explains how to use the `pastec-batch-index-search.py` script to search for similar images in the Pastec index.

## Overview

The script allows you to search for similar images in the Pastec index by processing a batch of query images. It reads image information from a CSV file, constructs file paths based on a base path and folder structure, and sends the images to the Pastec API for searching.

Key features:
- Process images in configurable batch sizes (default: 100 images per batch)
- Filter out self-matches (where the matched image ID is the same as the query image ID)
- Capture match scores and tags
- Detailed logging of the search process
- CSV output of search results

## Prerequisites

- Python 3.6 or higher
- Required Python packages: `aiohttp`, `asyncio`
- A running Pastec server (default: http://localhost:4212)
- A CSV file containing image information
- Image files organized in a folder structure
- Images already indexed in Pastec (using the batch add script)

## CSV Format

The script uses the same CSV format as the batch add script, with at least the following columns:
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
API_URL = "http://localhost:4212/index/searcher"  # Pastec API endpoint for searching
SOURCE_CSV = "images.csv"  # Default CSV filename
SEARCH_LOG_DIR = "Search_log"  # Directory for search logs
LOG_FILE = os.path.join(SEARCH_LOG_DIR, "pastec_search_log.txt")  # Log file for general messages
RESULTS_CSV = os.path.join(SEARCH_LOG_DIR, "pastec_search_results.csv")  # CSV file for search results
BASE_PATH = "/path/to/images"  # Base path where images are stored
BATCH_SIZE = 100  # Number of images to process in each batch
```

## Running the Script

Basic usage:

```bash
python pastec-batch-index-search.py
```

With command-line options:

```bash
# Run in test mode (process only the first 100 images)
python pastec-batch-index-search.py --testing

# Specify a different CSV file
python pastec-batch-index-search.py --csv my_images.csv

# Specify a different base path
python pastec-batch-index-search.py --base-path /path/to/my/images

# Combine options
python pastec-batch-index-search.py --testing --csv my_images.csv --base-path /path/to/my/images
```

## Output Files

The script generates several output files in the `Search_log` directory:

1. **Log file** (`pastec_search_log.txt`): Contains detailed information about the search process, including batch processing, API responses, and match results.

2. **Results CSV** (`pastec_search_results.csv`): Contains the results of the search process for each image, including:
   - Source_ID: ID of the query image
   - Source_Path: Path to the query image
   - Matched_Image_ID: ID of the matched image
   - Match_Score: Confidence score of the match
   - Match_Tag: Tag associated with the matched image (if any)

## Filtering Self-Matches

The script automatically filters out self-matches, where the matched image ID is the same as the query image ID. This prevents images from matching themselves in the results.

## Troubleshooting

### Common Issues

1. **File not found errors**: Check that your BASE_PATH and folder structure match what's in your CSV file. Make sure the filenames in the CSV match the actual filenames on disk.

2. **API connection errors**: Ensure that the Pastec server is running and accessible at the URL specified in API_URL.

3. **CSV parsing errors**: Verify that your CSV file has the expected column names and format. Check for any special characters or encoding issues.

4. **No matches found**: If you're not getting any matches, check that:
   - The images have been properly indexed using the batch add script
   - The images are of sufficient quality and size for Pastec to extract features
   - The search threshold in Pastec is appropriate for your use case

### Performance Tips

- The default batch size (100) is optimized for performance, but you can adjust it based on your system's capabilities.
- For very large datasets, consider splitting your CSV file into smaller chunks and processing them separately.
- If you're getting too many matches, you may need to filter the results further based on the match score.

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
   python pastec-batch-index-search.py
   ```

4. Check the `Search_log` directory for the log file and results CSV.

## Workflow

A typical workflow using both the batch add and batch search scripts would be:

1. Index your images using `pastec-batch-index-add.py`
2. Search for similar images using `pastec-batch-index-search.py`
3. Analyze the results in the `pastec_search_results.csv` file
