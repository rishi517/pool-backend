# Project Setup Guide

This guide will help you set up the project on your local machine for development and testing purposes.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python**: Make sure you have Python installed. The project uses Python 3.12.8, as indicated by the `.python-version` file.
- **Virtual Environment**: It's recommended to use a virtual environment to manage dependencies.
- **Firebase CLI**: Required for Firebase-related operations.

## Installation

1. **Clone the Repository**

   Clone the repository to your local machine using:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Set Up Virtual Environment**

   Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**

   Install the required Python packages using `pip`:

   ```bash
   pip install -r functions/requirements.txt
   ```

4. **Environment Variables**

   Create a `.env` file in the `functions` directory with the necessary environment variables.
   Variables:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_PHONE_NUMBER`
   - `RISHI_PHONE_NUMBER`
   - `OPENAI_API_KEY`



5. **Firebase Configuration**

   Ensure you have the Firebase CLI installed and configured. Use the `firebase.json` and `.firebaserc` files for Firebase setup.

6. **TWILIO Setup**

   Create a Twilio account and get the necessary credentials. Set up the WhatsApp sandbox and get the necessary credentials, putting the deployed functions in the sandbox webhook.

## Running the Project

1. **Deploy the Functions**

   Navigate to the `functions` directory and run the main script:

   ```
   firebase deploy --only functions
   ```

2. **Testing**

   Ensure all functionalities are working as expected. You may need to set up additional services or configurations as per your project requirements.

## Additional Information

- **Directory Structure**:
  - `functions/agents`: Contains various agent scripts.
  - `functions/tools`: Contains utility tools for the project.
  - `functions/lib`: Contains library files and utilities.
  - `functions/langchain_client.py`: Client for interacting with Langchain.

- **Logs**: Check `firebase-debug.log` for Firebase-related logs.

## Troubleshooting

- Ensure all dependencies are installed correctly.
- Verify environment variables are set up properly.
- Check logs for any errors or warnings.
