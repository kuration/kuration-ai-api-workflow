import os
import time
import logging
import pandas as pd
import requests
import json
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class KurationAPIProcessor:
    def __init__(self):
        self.base_url = "https://apistaging.kurationai.com/api/enterprise"
        self.api_key = os.getenv('KURATION_API_KEY')
        if not self.api_key:
            raise ValueError("KURATION_API_KEY environment variable is required")
        self.chat_id = os.getenv('KURATION_CHAT_ID')
        if not self.chat_id:
            raise ValueError("KURATION_CHAT_ID environment variable is required")
        
        self.headers = {
            'accept': 'application/json',
            'kur-api-key': self.api_key,
            'Content-Type': 'application/json'
        }

    def submit_company(self, company_data: Dict[str, Any]) -> str:
        """
        Submit company data to the API and return the row ID
        """
        try:
            payload = {
                "chat_id": self.chat_id,
                "company": {
                    "company name": company_data['company_name'],
                    "website url": company_data['website']
                }
            }
            
            response = requests.post(
                f"{self.base_url}/save_company_data",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            response_data = response.json()
            logger.info(f"Submit response: {response_data}")
            
            if response_data.get('error_detail'):
                raise Exception(f"API Error: {response_data['error_detail']}")
                
            row_id = response_data.get('row_id')
            if not row_id:
                raise Exception("No row_id in response")
                
            return str(row_id)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error submitting company data: {e}")
            raise

    def get_results(self, row_id: str) -> Dict[str, Any]:
        """
        Get results for a specific row ID
        """
        try:
            url = f"{self.base_url}/chat/{self.chat_id}/row/{row_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting results for row ID {row_id}: {e}")
            raise

    def extract_column_values(self, result: Dict[str, Any]) -> Tuple[Dict[str, str], bool]:
        """
        Extract column values from the API response into a flat dictionary
        Returns a tuple of (values_dict, is_still_loading)
        """
        values = {}
        is_still_loading = False
        
        # Handle the case where result is directly a list of columns
        columns = result if isinstance(result, list) else []
            
        for column in columns:
            column_name = column.get('column_name', '').strip()
            if not column_name:
                continue
                
            # Store the value directly with the original column name
            values[column_name] = column.get('value', '')
            
            # Check if this column is still loading
            if column.get('is_loading', False):
                is_still_loading = True
                
        return values, is_still_loading

    def process_csv(self, csv_path: str, check_interval: int = 30, max_wait_time: int = 1800):
        """
        Process the CSV file and handle API interactions
        check_interval: seconds to wait between checks for loading status
        max_wait_time: maximum seconds to wait for all results to complete
        """
        try:
            # Read CSV file
            df = pd.read_csv(csv_path)
            row_ids = []
            all_columns = set()  # To keep track of all possible columns
            results = []  # To store the latest results for each row

            # Submit all companies
            logger.info("Submitting companies to API...")
            for index, row in df.iterrows():
                company_data = {
                    'company_name': row['company_name'],
                    'website': row['website']
                }
                row_id = self.submit_company(company_data)
                row_ids.append(row_id)
                logger.info(f"Submitted company {row['company_name']} with row ID: {row_id}")

            # Initial wait
            logger.info("Waiting for initial processing...")
            time.sleep(30)

            # Keep checking until all results are complete or max time is reached
            start_time = time.time()
            loading_rows = row_ids.copy()
            iteration = 0
            
            while loading_rows and (time.time() - start_time) < max_wait_time:
                iteration += 1
                logger.info(f"\nCheck iteration {iteration}...")
                
                still_loading = []
                updated_results = []
                
                for row_id in loading_rows:
                    result = self.get_results(row_id)
                    values, is_loading = self.extract_column_values(result)
                    
                    # Update our record of all possible columns
                    all_columns.update(values.keys())
                    
                    # Store the complete result
                    result_entry = {
                        'row_id': row_id,
                        'values': values
                    }
                    updated_results.append(result_entry)
                    
                    if is_loading:
                        still_loading.append(row_id)
                        logger.info(f"Row {row_id} still has loading columns...")
                    else:
                        logger.info(f"Row {row_id} completed!")
                
                # Update our results with the latest data
                results = updated_results
                
                # Update loading_rows for next iteration
                loading_rows = still_loading
                
                if loading_rows:
                    remaining_time = max_wait_time - (time.time() - start_time)
                    logger.info(f"{len(loading_rows)} rows still loading. {int(remaining_time)}s remaining before timeout.")
                    logger.info("Waiting before next check...")
                    time.sleep(check_interval)

            # Prepare the final DataFrame
            final_data = []
            
            for row in df.iterrows():
                row_data = row[1].to_dict()  # Get original data
                
                # Find the corresponding result
                result = next((r for r in results if r['row_id'] == row_ids[row[0]]), None)
                
                if result:
                    # Add all API response columns
                    row_data.update(result['values'])
                    # Add row_id at the end
                    row_data['row_id'] = result['row_id']
                
                final_data.append(row_data)

            # Create DataFrame with all columns
            final_df = pd.DataFrame(final_data)
            
            # Organize columns: original columns first, then row_id, then all API columns
            original_cols = df.columns.tolist()
            api_cols = sorted(list(all_columns - set(original_cols) - {'row_id'}))
            final_cols = original_cols + ['row_id'] + api_cols
            
            # Reorder columns and save
            final_df = final_df[final_cols]
            output_path = 'api_results.csv'
            final_df.to_csv(output_path, index=False)
            logger.info(f"\nResults saved to {output_path}")
            
            # Log final status
            if loading_rows:
                logger.warning(f"\nTimeout reached! {len(loading_rows)} rows still had loading columns:")
                for row_id in loading_rows:
                    logger.warning(f"- Row ID: {row_id}")
            else:
                logger.info("\nAll rows completed successfully!")

        except Exception as e:
            logger.error(f"Error processing CSV: {e}")
            raise

def main():
    processor = KurationAPIProcessor()
    processor.process_csv('companies.csv')  # Adjust filename as needed

if __name__ == "__main__":
    main() 