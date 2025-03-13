import aiohttp
import asyncio
import csv
import os
import time
from datetime import datetime
import argparse
import base64
import json

# Constants
API_URL = "http://localhost:4212/index/images/"
SAVE_INDEX_URL = "http://localhost:4212/index/io"
SOURCE_CSV = "images.csv"  # Default CSV filename
ADD_LOG_DIR = "Add_log"  # Directory for add logs
LOG_FILE = os.path.join(ADD_LOG_DIR, "pastec_batch_index_add_log.txt")
MISSING_FILES_LOG = os.path.join(ADD_LOG_DIR, "pastec_batch_index_add_missing_files_log.txt")
RESULTS_CSV = os.path.join(ADD_LOG_DIR, "pastec_batch_index_add_log_results.csv")
BASE_PATH = "/path/to/images"  # Base path where images are stored

# CSV column mappings (customize these to match your CSV structure)
ID_COLUMN = "ID"  # Column containing the image ID
FILENAME_COLUMN = "Filename"  # Column containing the filename
FOLDER_COLUMN = "Folder"  # Column containing the folder name

BATCH_SIZE = 100  # 100 is the optimal batch size for adding images
SAVE_INTERVAL = 1000  # Save index every 1000 images, so make sure we don't lose the index in case pastec crashes
INDEX_PATH = "/pastec/build/pastec-index/pastec_index.dat"  # Path to save the index, this is passed in during the save command, needs to be accessible through the docker container and should be mapped as a volume on local machine

# Function to read the source CSV -- update encoding as necessary
def read_source_csv(file_path):
    with open(file_path, mode="r", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        return [{
            "ID": str(row[ID_COLUMN]),  # Convert to string to ensure consistency
            "filename": row[FILENAME_COLUMN],
            "folder": row.get(FOLDER_COLUMN, "")  # Use empty string if folder column is missing
        } for row in reader]

def ensure_log_directory():
    """Ensure the add log directory exists."""
    if not os.path.exists(ADD_LOG_DIR):
        os.makedirs(ADD_LOG_DIR)
        print(f"Created log directory: {ADD_LOG_DIR}")

# Function to append results to the results CSV
def append_to_results_csv(results):
    # Ensure the log directory exists
    ensure_log_directory()
    
    file_exists = os.path.isfile(RESULTS_CSV)
    with open(RESULTS_CSV, mode="a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["ID", "filename", "status", "response", "timestamp"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)

# Function to log messages
def log_message(message, log_file=LOG_FILE):
    timestamp = datetime.now().isoformat()
    
    # Ensure the log directory exists
    ensure_log_directory()
    
    with open(log_file, mode="a") as file:
        file.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

# Function to log missing files
def log_missing_file(file_path):
    timestamp = datetime.now().isoformat()
    message = f"[{timestamp}] {file_path}"
    
    # Ensure the log directory exists
    ensure_log_directory()
    
    with open(MISSING_FILES_LOG, mode="a") as file:
        file.write(f"{message}\n")
    # Also log to main log
    log_message(f"File not found: {file_path}")

# Function to save the index
async def save_index(session):
    try:
        payload = {
            "type": "WRITE",
            "index_path": INDEX_PATH
        }
        
        async with session.post(SAVE_INDEX_URL, json=payload) as response:
            response_text = await response.text()
            log_message(f"Index save response: {response_text}")
            return response_text
    except Exception as e:
        log_message(f"Error saving index: {str(e)}")
        return None

# Function to send the API request
async def send_index_request(session, image_id, file_path):
    try:
        # Construct the URL with the image ID
        url = f"{API_URL}{image_id}"
        
        # Read and send the image file directly
        with open(file_path, "rb") as image_file:
            data = image_file.read()
            headers = {
                'Content-Type': 'image/jpeg'
            }
            
            async with session.post(url, data=data, headers=headers) as response:
                response_text = await response.text()
                try:
                    return {
                        "status": response.status,
                        "response": response_text
                    }
                except Exception as e:
                    return {
                        "status": response.status,
                        "response": str(e)
                    }
    except FileNotFoundError:
        return {
            "status": 404,
            "response": f"File not found: {file_path}"
        }
    except Exception as e:
        return {
            "status": 500,
            "response": str(e)
        }

# Function to process a batch of images
async def process_batch(batch, test_mode=False):
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for item in batch:
            image_id = item["ID"]
            filename = item["filename"]
            folder = item["folder"]
            
            # Construct the full file path
            file_path = os.path.join(BASE_PATH, folder, filename)
            
            if not os.path.isfile(file_path):
                log_missing_file(file_path)
                results.append({
                    "ID": image_id,
                    "filename": filename,
                    "status": "ERROR",
                    "response": "File not found",
                    "timestamp": datetime.now().isoformat()
                })
                continue

            tasks.append((image_id, filename, send_index_request(session, image_id, file_path)))

        # Wait for all tasks to complete
        responses = await asyncio.gather(*[task[2] for task in tasks])
        
        # Process the responses
        for (image_id, filename, response), response_data in zip(tasks, responses):
            log_message(f"Response for {image_id}: {response_data}")
            
            results.append({
                "ID": image_id,
                "filename": filename,
                "status": "SUCCESS" if response_data["status"] == 200 else "ERROR",
                "response": response_data["response"],
                "timestamp": datetime.now().isoformat()
            })

    return results

# Main function
async def main(test_mode):
    # Ensure the log directory exists
    ensure_log_directory()
    
    log_message("Starting Pastec batch indexing process.")
    images = read_source_csv(SOURCE_CSV)
    total_images = len(images)
    processed_images = 0
    
    if test_mode:
        log_message(f"Test mode is enabled. Processing the first 100 images only.")
        images = images[:100]
    
    log_message(f"Total images to process: {len(images)}")
    
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(images), BATCH_SIZE):
            batch = images[i:i + BATCH_SIZE]
            log_message(f"Processing batch {i // BATCH_SIZE + 1} (images {i + 1} to {i + len(batch)})...")
            
            batch_results = await process_batch(batch, test_mode=test_mode)
            
            # Append results after processing each batch
            if batch_results:
                append_to_results_csv(batch_results)
                log_message(f"Batch {i // BATCH_SIZE + 1} results saved to {RESULTS_CSV}.")
            
            # Update processed images count
            processed_images += len(batch)
            
            # In test mode, save after processing completes
            if test_mode and i + len(batch) >= 100:
                log_message("Test mode: Stopping after processing 100 images.")
                log_message("Saving index...")
                await save_index(session)
                break
            
            # In normal mode, save every SAVE_INTERVAL images
            if not test_mode and processed_images % SAVE_INTERVAL == 0:
                log_message(f"Saving index after processing {processed_images} images...")
                await save_index(session)
    
    # Save index one final time at the end if not in test mode
    if not test_mode and processed_images > 0:
        async with aiohttp.ClientSession() as session:
            log_message("Saving final index...")
            await save_index(session)
    
    log_message("Indexing completed.")

# Command-line interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform Pastec API batch indexing.")
    parser.add_argument("--testing", action="store_true", default=False, 
                      help="Enable test mode to process only the first 100 images.")
    parser.add_argument("--csv", type=str, default=SOURCE_CSV,
                      help=f"Path to the CSV file containing image information (default: {SOURCE_CSV})")
    parser.add_argument("--base-path", type=str, default=BASE_PATH,
                      help=f"Base path where images are stored (default: {BASE_PATH})")
    args = parser.parse_args()
    
    # Override constants if provided via command line
    if args.csv != SOURCE_CSV:
        SOURCE_CSV = args.csv
    if args.base_path != BASE_PATH:
        BASE_PATH = args.base_path
    
    asyncio.run(main(test_mode=args.testing))
