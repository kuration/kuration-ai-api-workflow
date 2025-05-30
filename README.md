# KurationAI API Workflow

This script processes company data through the KurationAI API, extracting detailed information and creating a structured CSV output.

## Features

- Batch process multiple companies through KurationAI API
- Automatic handling of API rate limits and processing times
- Converts nested JSON responses into a flat CSV structure
- Progress logging and error handling
- Configurable timeout and check intervals

## Prerequisites

- Python 3.6+
- KurationAI API key
- Input CSV file with company data

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/KurationAI-API-workflow.git
cd KurationAI-API-workflow
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
```bash
cp .env.example .env
# Edit .env with your API key
```

## Usage

1. Prepare your input CSV file with the following columns:
   - `company_name`: Name of the company
   - `website`: Company website URL

Example `companies.csv`:
```csv
company_name,website
Stripe,https://stripe.com
Shopify,https://shopify.com
```

2. Run the script:
```bash
python kuration_api_processor.py
```

<img width="619" alt="Screenshot 2025-04-08 at 5 43 05 PM" src="https://github.com/user-attachments/assets/ef6ee690-ec96-4774-9b25-298deea878ba" />


The script will:
- Submit companies to the API
- Wait for initial processing (30 seconds)
- Check status every 30 seconds
- Generate `api_results.csv` with all extracted data

<img width="808" alt="Screenshot 2025-04-08 at 5 42 53 PM" src="https://github.com/user-attachments/assets/d1be3317-9e94-40eb-b74c-97f859310a53" />


## Output

The script generates `api_results.csv` containing:
- Original input columns (company_name, website)
- row_id (API reference)
- All extracted data fields as separate columns

<img width="881" alt="Screenshot 2025-04-08 at 5 43 31 PM" src="https://github.com/user-attachments/assets/26e2cd63-6ab1-4f36-833a-996982941c8d" />

Example output fields:
- Company Headcount
- Industry
- Company Address
- Email contacts
- And many more...

## Configuration

Default settings in the script:
- Initial wait time: 30 seconds
- Check interval: 30 seconds
- Maximum wait time: 1800 seconds (30 minutes)

To modify these settings, edit the parameters in `kuration_api_processor.py`:
```python
processor.process_csv('companies.csv', 
    check_interval=30,  # seconds between status checks
    max_wait_time=1800  # maximum total wait time
)
```

## Error Handling

The script includes:
- Automatic retry on API failures
- Detailed logging of all operations
- Status updates for each company
- Timeout handling for long-running processes

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- KurationAI for providing the API
- Contributors and maintainers

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 
