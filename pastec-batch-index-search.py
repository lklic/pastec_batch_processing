import aiohttp
import asyncio
import csv
import os
import time
import argparse
from datetime import datetime

# Constants
API_URL = "http://localhost:4212/index/searcher"
SOURCE_CSV = "images.csv"  # Default CSV filename
SEARCH_LOG_DIR = "Search_log"  # Directory for search logs
LOG_FILE = os.path.join(SEARCH_LOG_DIR, "pastec_search_log.txt")
RESULTS_CSV = os.path.join(SEARCH_LOG_DIR, "pastec_search_results.csv")
BASE_PATH = "/path/to/images"  # Base path where images are stored

# CSV column mappings (customize these to match your CSV structure)
ID_COLUMN = "ID"  # Column containing the image ID
FILENAME_COLUMN = "Filename"  # Column containing the filename
FOLDER_COLUMN = "Folder"  # Column containing the folder name

BATCH_SIZE = 100  # Number of images to process in each batch

def ensure_log_directory():
    """Ensure the search log directory exists."""
    if not os.path.exists(SEARCH_LOG_DIR):
        os.makedirs(SEARCH_LOG_DIR)
        print(f"Created log directory: {SEARCH_LOG_DIR}")

def read_source_csv(file_path):
    """Read and parse the source CSV file."""
    records = []
    with open(file_path, mode="r", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            records.append({
                "ID": str(row[ID_COLUMN]),  # Convert to string to ensure consistency
                "filename": row[FILENAME_COLUMN],
                "folder": row.get(FOLDER_COLUMN, "")  # Use empty string if folder column is missing
            })
    return records

def append_to_results_csv(results):
    """Append results to the output CSV file."""
    file_exists = os.path.isfile(RESULTS_CSV)
    with open(RESULTS_CSV, mode="a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=[
            "Source_ID",
            "Source_Path",
            "Matched_Image_ID",
            "Match_Score",
            "Match_Tag"
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)

def log_message(message, log_file=LOG_FILE):
    """Log a message to both file and console."""
    timestamp = datetime.now().isoformat()
    
    # Ensure the log directory exists
    ensure_log_directory()
    
    with open(log_file, mode="a") as file:
        file.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

async def send_search_request(session, file_path):
    """Send a search request to the Pastec API."""
    try:
        async with session.post(API_URL, data=open(file_path, "rb")) as response:
            response_text = await response.text()
            log_message(f"Raw response for {file_path}: {response_text}")

            if response.status == 200:
                try:
                    # Try to parse the JSON response
                    import json
                    response_data = json.loads(response_text)
                    return response_data
                except json.JSONDecodeError:
                    # Fallback to ast.literal_eval if JSON parsing fails
                    try:
                        import ast
                        response_data = ast.literal_eval(response_text)
                        return response_data
                    except Exception as parse_error:
                        return {"error": f"Failed to parse response: {str(parse_error)}", "raw_response": response_text}
            else:
                return {"error": f"HTTP {response.status}", "response": response_text}
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except Exception as e:
        return {"error": str(e)}

async def process_batch(batch, starting_index, test_mode=False):
    """Process a batch of images."""
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for idx, item in enumerate(batch, start=starting_index):
            # Construct the full file path
            file_path = os.path.join(BASE_PATH, item["folder"], item["filename"])
            
            if not os.path.isfile(file_path):
                log_message(f"File not found: {file_path}")
                continue

            tasks.append((item, send_search_request(session, file_path)))

            if test_mode and idx - starting_index + 1 >= 100:
                log_message("Test mode: Stopping after processing 100 images.")
                break

        # Await all tasks concurrently
        responses = await asyncio.gather(*[task[1] for task in tasks])

        # Process the responses
        for (item, _), response in zip(tasks, responses):
            source_id = item["ID"]
            file_path = os.path.join(BASE_PATH, item["folder"], item["filename"])
            
            log_message(f"Response for {source_id}: {response}")

            try:
                if "error" not in response:
                    # Check if we have a valid search response
                    if isinstance(response, dict) and response.get("type") == "SEARCH_RESULTS":
                        search_results = response.get("results", [])
                        
                        # Only process if there are matches
                        if search_results:
                            # Add a row for each match, excluding self-matches
                            for result in search_results:
                                matched_id = result["image_id"]
                                
                                # Skip if the matched ID is the same as the source ID
                                if str(matched_id) == source_id:
                                    log_message(f"Skipping self-match for ID {source_id}")
                                    continue
                                    
                                results.append({
                                    "Source_ID": source_id,
                                    "Source_Path": file_path,
                                    "Matched_Image_ID": matched_id,
                                    "Match_Score": result["score"],
                                    "Match_Tag": result.get("tag", "")  # Include tag if available
                                })
                else:
                    log_message(f"Error for {source_id}: {response['error']}")
            except Exception as e:
                log_message(f"Error processing response for {source_id}: {str(e)}")

    return results

async def main(test_mode):
    """Main function to coordinate the search process."""
    # Ensure the log directory exists
    ensure_log_directory()
    
    log_message("Starting Pastec batch search process.")
    
    try:
        images = read_source_csv(SOURCE_CSV)
        total_images = len(images)

        if test_mode:
            log_message(f"Test mode is enabled. Processing the first 100 images only.")
            images = images[:100]

        log_message(f"Total images to process: {len(images)}")

        total_matches = 0
        
        for i in range(0, len(images), BATCH_SIZE):
            batch = images[i:i + BATCH_SIZE]
            log_message(f"Processing batch {i // BATCH_SIZE + 1} (images {i + 1} to {i + len(batch)})...")

            batch_results = await process_batch(batch, starting_index=i, test_mode=test_mode)
            
            if batch_results:
                append_to_results_csv(batch_results)
                total_matches += len(batch_results)
                log_message(f"Batch {i // BATCH_SIZE + 1} results saved to {RESULTS_CSV}. Found {len(batch_results)} matches.")

            if test_mode and i + len(batch) >= 100:
                log_message("Test mode: Stopping after processing 100 images.")
                break

        log_message(f"Search completed. Processed {min(total_images, 100 if test_mode else total_images)} images. Found {total_matches} total matches.")
        
    except Exception as e:
        log_message(f"Error during search process: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform Pastec API batch searches for images.")
    parser.add_argument("--testing", action="store_true", help="Enable test mode to process only the first 100 images.")
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
