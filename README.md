# Gmail Python App

## Overview
This project is a Python application that integrates with the Gmail API, allowing users to perform various email operations such as reading, sending, replying to emails, managing labels, and deleting emails.

## Project Structure
```
gmail-python-app
├── src
│   ├── email_full_integ.py       # Main functionality for interacting with the Gmail API
│   ├── gmail
│   │   ├── __init__.py           # Initializes the gmail package
│   │   ├── auth.py                # Handles authentication with the Gmail API
│   │   ├── mail.py                # Contains functions for email operations
│   │   └── labels.py              # Manages Gmail labels
│   └── utils
│       └── helpers.py             # Utility functions for various tasks
├── tests
│   └── test_email_integ.py        # Unit tests for email integration functionality
├── .gitignore                     # Specifies files to ignore in Git
├── requirements.txt               # Lists project dependencies
├── setup.cfg                      # Configuration settings for the project
└── README.md                      # Documentation for the project
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd gmail-python-app
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
1. Ensure you have set up your Google Cloud project and enabled the Gmail API.
2. Update the `CLIENT_ID`, `CLIENT_SECRET`, and `REDIRECT_URI` in `src/email_full_integ.py` with your credentials.
3. Run the application:
   ```
   python src/email_full_integ.py
   ```

## Features
- **Read Emails**: Fetch and display the latest emails from your Gmail account.
- **Send Email**: Compose and send emails to specified recipients.
- **Reply to Emails**: Reply to existing emails with a simple interface.
- **Manage Labels**: Create, list, and delete labels in your Gmail account.
- **Delete Emails**: Permanently delete emails from your inbox.

## Testing
To run the tests, use the following command:
```
pytest tests/test_email_integ.py
```

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.