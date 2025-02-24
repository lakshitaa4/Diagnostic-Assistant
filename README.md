# Diagnostic Assistant

## Overview

Diagnostic Assistant is a Streamlit application designed to:

*   **Assist medical professionals** in making informed and efficient diagnoses.
*   **Leverage Google's Gemini 2.0 Flash AI model** to analyze medical data.
*   **Process diverse input formats:**
    *   Medical images (PNG, JPG, JPEG)
    *   PDF reports (converted to images)
*   **Generate comprehensive diagnostic outputs:**
    *   Ranked list of potential diagnoses with probability scores
    *   Supporting evidence and reasoning for each diagnosis
    *   Identification of relevant risk factors
    *   Links to reputable medical articles related to the primary diagnosis
    *   Image analysis details
*   **Create PDF reports** summarizing the analysis, including:
    *   Patient information
    *   Primary diagnosis details
    *   Image analysis findings
    *   Doctor's notes and signature
*   **Clearly state its limitations** with a prominent disclaimer: This tool is for educational purposes only and should not replace professional medical advice.

## Features

*   **Versatile Medical Data Input:**
    *   Accepts direct uploads of medical images in PNG, JPG, and JPEG formats.
    *   Processes PDF reports by converting them to images for analysis.
*   **AI-Powered Diagnostic Engine:**
    *   Leverages the Gemini 2.0 Flash model for rapid and insightful diagnostic suggestions.
    *   Provides a ranked list of the top 3-5 potential diagnoses with probability scores.
*   **Comprehensive Evidence-Based Reasoning:**
    *   Explains the reasoning behind each diagnosis, citing specific evidence from the patient data (including images).
    *   Identifies relevant risk factors contributing to each diagnosis.
*   **Exploration of Alternative Diagnoses:**
    *   Considers and discusses alternative diagnoses, explaining why they are less likely.
*   **Access to Reputable Medical Knowledge:**
    *   Automatically searches for and displays relevant articles from trusted sources like Mayo Clinic, WebMD, AIIMS, and NIH.
*   **Detailed Image Analysis:**
    *   Analyzes the uploaded medical images to identify key features and abnormalities.
    *   Provides insights into the image type and relevant findings.
*   **Customizable PDF Report Generation:**
    *   Generates a downloadable PDF report summarizing the diagnostic findings.
    *   Includes patient information, primary diagnosis details, image analysis, and doctor's notes.
*   **User-Centric Design:**
    *   Intuitive Streamlit interface with a tabbed layout for organized information.
    *   Clear and concise presentation of results to aid in decision-making.
    *   Accessibility of key functions and disclaimers at any point of usage.
*  **Important Tool Use disclaimer**:
    *    Clearly stated to never be used a medical alternative, and only use for professional medical uses.

## Installation

To set up the Medical Diagnosis Assistant, follow these detailed steps:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/lakshitaa4/Diagnostic-Assistant.git
    ```

2.  **Navigate to the project directory:**

    ```bash
    cd Diagnostic-Assistant
    ```

3.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv env
    ```

4.  **Activate the virtual environment:**

    *   **On macOS and Linux:**

        ```bash
        source env/bin/activate
        ```

    *   **On Windows:**

        ```bash
        env\Scripts\activate
        ```

5.  **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

6.  **Configure API Key:**

    *   Obtain a Gemini API key from [Google AI Studio](https://makersuite.google.com/).
    *   Edit the `Diag_Assist.py` file and replace the placeholder API key ( `"your-API-KEY"`) with your actual Gemini API key.

7.  **Install and Configure Poppler (Required for PDF to Image Conversion):**

    *   This project uses the `pdf2image` library to convert PDF pages into images, enabling the analysis of PDF reports. Follow these instructions to set up Poppler, a prerequisite for `pdf2image`:
    *   **Download and Setup Guide Follow these instructions from [pdf2image's GitHub repository](https://github.com/Belval/pdf2image).: The first key instruction is Downloading the correct version of the files. The steps for download are in the GitHub, as mentioned before. Then, for each operating system there are steps to follow, so please do that!
    *   Locate and copy the "bin" folder path, like `C:\Users\your_username\Downloads\poppler-xx.xx.x\bin`, this is just an example
    *   Then Navigate to bin folder, and copy address
    *   **PATH Set-Up**:The next key part is adding to your system's PATH. Here’s how:
        1.  Open the "System" control panel (search for "System" in the Start Menu).
        2.  Click "Advanced system settings".
        3.  Click "Environment Variables...".
        4.  In the "System variables" section, find the `Path` variable and click "Edit...".
        5.  Click "New" and add the path to the Poppler's `bin` directory (e.g., `C:\Poppler\poppler-xx.xx.x\bin`).
        6.  Click "OK" to save the changes.
        7.  **Restart your computer** for the changes to take effect. **Important**: Follow the specific instructions for your operating system, especially on Windows, and add the `bin` folder to the `PATH` to easily allow PDF files to be used on Medical-Diagnosis-Assistant. 
8.  **Install and Configure wkhtmltopdf (Required for PDF Report Generation):**

    * To enable the generation of PDF reports summarizing the analysis, follow these steps to install and configure `wkhtmltopdf`:
        *   **Download from official website:** Download and install wkhtmltopdf version 0.12.6 (recommended for compatibility) from the official website: [https://wkhtmltopdf.org/downloads.html](https://wkhtmltopdf.org/downloads.html). Select the installer that corresponds to your specific operating system (Windows, macOS, Linux) and system architecture (64-bit or 32-bit).
        Then do the `bin` address setup in PATH as you did for `pdf2image`.
*   **Path Addition**: It is similarly required to the PATH of your system, as PDF2image needs to do. To set it up properly, please follow the steps and do exactly as is said! Ensure that the system architecture is correct to have this step fully function.


## Usage

To run the Medical Diagnosis Assistant:

1.  **Activate the virtual environment** (if you created one):

    *   **On macOS and Linux:**

        ```bash
        source env/bin/activate
        ```

    *   **On Windows:**

        ```bash
        env\Scripts\activate
        ```

2.  **Run the Streamlit application:**

    ```bash
    streamlit run Diag_Assist.py
    ```

3.  **Access the application:** Open your web browser and go to the address displayed in the terminal (usually `http://localhost:8501`).

## Using the application
This section demonstrates how to use the Medical Diagnosis Assistant through the graphical user interface (GUI).

**1: Diagnosing a Condition from a Medical Image**

1.  **Upload a medical image:** Click on the "Reports & Scans" file uploader and select a PNG, JPG, or JPEG image containing a medical scan (e.g., X-ray, MRI).
2.  **Provide patient details:** In the "Patient Details: History and Symptoms" text area, enter relevant information about the patient's medical history, symptoms, and any other pertinent details. Be as specific as possible to help the AI provide accurate diagnoses.
3.  **Generate diagnosis:** Click the "Generate Diagnosis" button.
4.  **Review the results:** Explore the generated diagnoses, supporting evidence, image analysis, and relevant articles in the tabbed interface.

**2: Analyzing a PDF Report**

1.  **Upload a PDF report:** Click on the "Reports & Scans" file uploader and select a PDF file containing a medical report.
2.  **Provide patient details:** In the "Patient Details: History and Symptoms" text area, enter relevant information about the patient, as extracted from the PDF or from other sources.
3.  **Generate diagnosis:** Click the "Generate Diagnosis" button.
4.  **Review the results:** Explore the generated diagnoses, supporting evidence, image analysis (converted from the PDF), and relevant articles in the tabbed interface.

**3: Generating a PDF Report**

1.  **Complete a diagnosis:** Follow the steps in Example 1 or Example 2 to generate a diagnosis.
2.  **Add doctor's notes:** In the "Additional Information" tab, add any relevant notes or observations in the "Doctor's Notes" text area.
3.   **Add doctor's signature**: Input your signiture
4.  **Generate PDF report:** Click the "Generate PDF Report" button.
5.  **Download the report:** Click the "Download PDF report" button to download a PDF file containing the diagnosis summary, patient information, image analysis, and doctor's notes.

## License

MIT

## Contact

For any questions or issues, feel free to reach out via:
- Email: [lakshita0000001@gmail.com](lakshita0000001@gmail.com)

