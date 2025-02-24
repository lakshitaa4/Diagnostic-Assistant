import os
import mimetypes
import pathlib
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import json
import io  # Import io
from pdf2image import convert_from_path  # Import pdf2image
import pdfkit
import base64

# This section defines the system instruction for Gemini Pro.

# Define the system instruction for Gemini Pro
# This is like setting the "persona" or role of the AI"""

sys_ins = """You are a highly skilled and experienced diagnostic assistant AI, designed to aid medical professionals in accurately 
and efficiently diagnosing diseases. Your primary function is to analyze patient data and provide a ranked list of 
potential diagnoses with supporting evidence, while also considering and ruling out alternative possibilities.
Analyze the following medical data and generate a list of potential diagnoses to assist medical professionals. Your response must be comprehensive and adhere to the following guidelines:

1.  **Data Analysis:** Carefully analyze all provided patient information, including medical history, symptoms, physical examination findings, and any relevant details.

2.  **Differential Diagnosis:** Generate a ranked list of the top 3-5 most likely diagnoses, along with a probability score (0-100%) for each. Ensure probabilities are realistic, reflecting the likelihood of each diagnosis given the data. Mention the primary diagnosis as "Primary Diagnoses" under this section.

3.  **Evidence-Based Reasoning (CRITICAL):** For each potential diagnosis, provide a clear and concise explanation of your reasoning. **Crucially, you MUST cite *specific* evidence directly from the provided patient data to support your conclusion.** Avoid general statements; instead, point to precise details in the patient's symptoms, history, or examination findings that support the diagnosis. Explain why you think the patient has this condition.

4.  **Alternative Diagnoses:** Discuss at least one alternative diagnosis that could also explain the patient's symptoms. Explain why that diagnosis is considered less likely than the top diagnoses, citing specific evidence against it.

5.  **Risk Factor Identification:** Identify any relevant risk factors present in the patient's history or lifestyle that may contribute to the potential diagnoses.

6.  **Severity Assessment:** Assess the potential severity of each diagnosis (e.g., mild, moderate, severe, life-threatening) and explain your reasoning.

7.  **Follow-Up Recommendations:** Suggest 2-3 relevant follow-up questions, examinations, or laboratory tests that could help to further refine the diagnosis and rule out other possibilities.

8.  **Bias Awareness and Mitigation (IMPORTANT):** Identify any potential biases that might be present in your reasoning due to limitations in the provided information, the prompt, or your training data. Present the biases as bullet points. Include recommendations that will give more information regarding each specific bias in order to potentially help to reduce the impact of it.
    Don't throw risk factors like 'anxiety' until 80 % sure
9. Make reference to the image output so that the information is correctly used. If the image output is not provided or does not aid you in providing more information to what can already be derived, then note that and add the following to 'relevant details': 'Analysis of images was not useful in this case.'

10. If the uploaded images are non-medical, respond with the following format. Make sure you analyze what exactly is in the image in a "image_analysis" under "IMAGE_ANALYSIS" with confidence_level as 10. Include {"Answer": "Not applicable."} even when its a non medical image, or you were not asked a question.
```json
{
  "patient_information": {
    "age": null,
    "symptoms": null,
    "relevant_details": "Analysis of images was not useful in this case."
  },
  "IMAGE_ANALYSIS": {
    "image_type": "Non-medical image",
    "image_analysis": "Describe the image here."
  },
  "ans_to_ques": {"Answer": "Not applicable."},
  "differential_diagnosis": [],
  "alternative_diagnoses": [],
  "follow_up_recommendations": [],
  "biases": [
   {"bias": "Lack of patient-specific information limits diagnostic accuracy.", "recommendation": "Obtain a complete patient history, including age, symptoms,  and relevant medical background."},
   {"bias": "Absence of medical examination data hinders comprehensive assessment.", "recommendation": "Conduct a thorough physical examination and gather vital signs."},
   {"bias": "Reliance on image data alone may lead to incomplete or inaccurate conclusions.", "recommendation": "Integrate image findings with other diagnostic modalities, such as laboratory tests and clinical assessments."}
  ],
  "articles": [],
  "confidence_level": 10,
  "important_note": "This information is intended for informational and educational purposes only and does not constitute medical advice. It is essential to consult with a qualified healthcare professional for any health concerns and should not be used as a substitute for a consultation with a healthcare provider."
}
11. If the prompt has a question, answer that in "ans_to_ques".

12. Search the google for articles on the most likely diagnosis from websites like "Mayo Clinic", "WebMD", "AIIMS", "NIH(.gov)".

13.  Ensure the JSON is properly structured, formatted, and valid. You **MUST** start and end with `{}` brackets and follow this exact schema:

```json
{
  
  "patient_information": {
    "age": [Age],
    "symptoms": "[Symptoms]",
    "relevant_details": "[Any Other Pertinent Information]"
  },
  "IMAGE_ANALYSIS": {
    "image_type": "[Image Type]",
    "image_analysis": "[Image Analysis]"
  }
  "ans_to_ques": {"[Answer to Question]"}
  "differential_diagnosis": [
    {
      "diagnosis": "[Diagnosis Name]",
      "probability": [Probability Percentage (0-100)],
      "reasoning": "[Explanation with SPECIFIC EVIDENCE CITATIONS]",
      "severity": "[Severity Assessment]",
      "risk_factors": "[List of Risk Factors]"
    },
    {
      "diagnosis": "[Diagnosis Name]",
      "probability": [Probability Percentage (0-100)],
      "reasoning": "[Explanation with SPECIFIC EVIDENCE CITATIONS]",
      "severity": "[Severity Assessment]",
      "risk_factors": "[List of Risk Factors]"
    },
    ...
  ],
  "alternative_diagnoses": [
    {
      "diagnosis": "[Alternative Diagnosis Name]",
      "reasoning_against": "[Explanation of why this diagnosis is less likely]"
    }
  ],
  "follow_up_recommendations": [
    "[Follow-Up Recommendation 1]",
    "[Follow-Up Recommendation 2]",
    "[Follow-Up Recommendation 3]"
  ],
  "biases": [
   {"bias": "[Explanation of limitation]", "recommendation": "[Recommendation to obtain more information related to the specific bias]"}
  ],
  "articles": ["Google suggestion"],
  "confidence_level": [Confidence Percentage (0-100)],
  "important_note": "This information is intended for informational and educational purposes only and does not constitute medical advice. It is essential to consult with a qualified healthcare professional for any health concerns and should not be used as a substitute for a consultation with a healthcare provider."
}
Give output in JSON format
"""

# Initialize Gemini API
API_KEY = "your-API-KEY"  # Replace with your Gemini API Key
client = genai.Client(api_key=API_KEY)

google_search_tool = Tool(google_search=GoogleSearch())

# Function to get MIME type
def get_mime_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type if mime_type else "application/octet-stream"

# Function to upload and process images
def image_upload():
    images = []
    uploaded_files = st.file_uploader("Reports & Scans", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True)

    if uploaded_files:
        for file in uploaded_files:
            file_path = os.path.join("uploads", file.name)
            os.makedirs("uploads", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            mime_type = mimetypes.guess_type(file_path)[0]
            if mime_type in ["image/png", "image/jpg", "image/jpeg"]:
                image = Image.open(file)
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                image_part = genai.types.Part.from_bytes(
                    data=img_byte_arr,
                    mime_type="image/png"
                )
                images.append((image, image_part, file_path))
            elif mime_type == "application/pdf":
                pdf_images = pdf_to_images(file_path)
                for img in pdf_images:
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    img_byte_arr = img_byte_arr.getvalue()
                    image_part = genai.types.Part.from_bytes(
                        data=img_byte_arr,
                        mime_type="image/png"
                    )
                    images.append((img, image_part, "pdf page"))
            else:
                st.warning(f"Unsupported file type: {mime_type}")
    return images

# Function to call Gemini API
def call_gemini(contents, sys_ins):
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=contents,
            config=GenerateContentConfig(
                system_instruction=sys_ins,
                temperature=1,
                tools=[google_search_tool],
            ),
        )

        r = response.text        
        a = r.strip('```')
        if a.startswith("json"):
            json_string = a[4:].strip()  # Remove "json" and any leading/trailing whitespace
        else:
            json_string = a
        print("The json is:", json_string)
        return json_string
    except Exception as e:
        st.error(f"\u274C Error calling Gemini API: {e}")
        return None

def parse_gemini_response(response_text):
    """Parses the Gemini response, tries harder to fix, and returns None on failure."""
    response_text = response_text.strip()  # Remove leading/trailing whitespace
    response_text = response_text.replace("\n", "")  # Remove newlines
    response_text = response_text.replace("\\", "") #Remove escape characters
    response_text = response_text.replace('`', "")  # Remove backticks
    response_text = response_text.replace("...", "")  # Remove ellipses.

    # Add missing braces if necessary
    if not response_text.startswith("{"):
        response_text = "{" + response_text
    if not response_text.endswith("}"):
        response_text = response_text + "}"

    try:
        json_data = json.loads(response_text)
        return json_data
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON Decode Error: {e}.  Completely invalid JSON response.  Check the prompt and model behavior.  Returning None.")
        return None

# Function to display results
def adjust_layout():
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 100%;
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .appview-container {
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

from pdf2image import convert_from_path
import io

def pdf_to_images(pdf_path):
    """Converts a PDF to a list of PIL Images."""
    try:
        images = convert_from_path(pdf_path)
        return images
    except Exception as e:
        st.error(f"Error converting PDF to images: {e}. Is Ghostscript installed?")
        return []

def display_results(json_data, images):
    if not json_data:
        st.error("\u274C No valid data to display. Please check the prompt and model's output.")
        return

    image_type = json_data.get("IMAGE_ANALYSIS", {}).get("image_type", "") # Get image_type and set default to ""
    if  image_type == "Non-medical image":
        st.warning("The uploaded image appears to be non-medical or no image data was uploaded. Please upload a medical image or PDF for analysis.")
        return

    # --- Tabbed Interface ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
        ["Patient Information", "Diagnosis", "Other Diagnoses", "Alternative Diagnoses", "Image & Analysis", "Articles", "Additional Info", "Confidence"])

    with tab1:
        st.header("Patient Information")
        st.write(f"**Age:** {json_data.get('patient_information', {}).get('age', 'N/A')}")
        st.write(f"**Symptoms:** {json_data.get('patient_information', {}).get('symptoms', 'N/A')}")
        st.write(f"**Relevant Details:** {json_data.get('patient_information', {}).get('relevant_details', 'N/A')}")

    with tab2:
        st.header("Diagnosis")
        differential_diagnosis = json_data.get('differential_diagnosis', []) # Get differential_diagnosis and set default to empty list
        if differential_diagnosis: #Check if its empty!
            primary_diagnosis = max(differential_diagnosis, key=lambda x: x['probability'])
            st.subheader(f"Primary Diagnosis: {primary_diagnosis['diagnosis']}")
            st.write(f"**Probability:** {primary_diagnosis['probability']}%")
            st.write(f"**Reasoning:** {primary_diagnosis['reasoning']}")
            st.write(f"**Severity:** {differential_diagnosis[0].get('severity', 'N/A')}") #fixed code!
            st.write(f"**Risk Factors:** {differential_diagnosis[0].get('risk_factors', 'N/A')}") #fixed
        else:
            st.write("No diagnoses found.")

    with tab3:
        st.header("Other Diagnoses")
        differential_diagnosis = json_data.get('differential_diagnosis', [])
        if differential_diagnosis:
            for diagnosis in differential_diagnosis:
                if diagnosis and isinstance(diagnosis, dict) and 'severity' in diagnosis:  # Comprehensive check
                    with st.expander(f"Diagnosis: {diagnosis['diagnosis']} (Probability: {diagnosis['probability']}%)"):
                        st.write(f"**Reasoning:** {diagnosis['reasoning']}")
                        st.write(f"**Severity:** {diagnosis['severity']}")
                        st.write(f"**Risk Factors:** {diagnosis['risk_factors']}")
                else:
                    st.write("A malformed diagnosis was found, please evaluate your JSON") # Inform the user
        else:
            st.write("No other diagnoses to display.") # Inform the user

    with tab4:
        st.header("Alternative Diagnoses")
        alternative_diagnoses = json_data.get("alternative_diagnoses", []) #Get this!
        if alternative_diagnoses:
            for diagnosis in alternative_diagnoses:
                with st.expander(f"Diagnosis: {diagnosis['diagnosis']}"):
                    st.write(f"**Reasoning Against:** {diagnosis['reasoning_against']}")
        else:
             st.write("No alternative diagnoses to display.") # Inform the user

    with tab5:
        st.header("Image and Analysis")
        for img_data in images:
            st.image(img_data[0], caption="Uploaded Image", use_container_width=True) #Show all images

        st.subheader("Image Analysis")
        st.write(f"**Image Type:** {json_data.get('IMAGE_ANALYSIS', {}).get('image_type', 'N/A')}")
        st.write(f"**Analysis:** {json_data.get('IMAGE_ANALYSIS', {}).get('image_analysis', 'N/A')}")

    with tab6:
        st.header("Articles")
        articles = json_data.get('articles', [])
        if articles:
            for article in articles:
                st.write(f"- {article}")
        else:
            st.write("No articles found.")

    with tab7:
        st.header("Additional Information")

        if json_data.get("ans_to_ques"):
            st.subheader("Answer to Question")
            for question, answer in json_data["ans_to_ques"].items():
                st.write(f"**{question}:** {answer}")

        st.subheader("Biases")
        for bias_info in json_data.get('biases', []):
            st.write(f"**Bias:** {bias_info['bias']}")
            st.write(f"**Recommendation:** {bias_info['recommendation']}")
    

    with tab8:
        st.header("Confidence Level")
        st.write(f"**Confidence Level:** {json_data.get('confidence_level', 'N/A')}%")

from datetime import datetime
def main():
    # Adjust layout to increase working space
    adjust_layout()

    # Make the title clickable
    title = """
        <div style="display: flex; justify-content: center;">
            <h1 style='display: inline;'>
                <a href="" target="_self" style="text-decoration: none;">🩺 Medical Diagnosis Assistant 💊</a>
            </h1>
        </div>
    """
    st.markdown(title, unsafe_allow_html=True)
    # Add CSS to remove link styling and prevent new tab opening
    st.markdown("""
        <style>
        a {
            color: inherit; /* blue colors for links too */
            text-decoration: none; /* no underline */
        }
        a:hover {
            text-decoration: none;
        }
        a:active {
            color: inherit;
        }
        </style>
    """, unsafe_allow_html=True)

    images = image_upload()
    prompt = st.text_area("Patient Details: History and Symptoms", "Just give output based on image.")  # User prompt is now in the flow

    # Initialize session state *before* the "Generate Diagnosis" button
    if 'show_followup' not in st.session_state:
        st.session_state.show_followup = False

    if st.button("Generate Diagnosis"):
        if not images:
            st.warning("Please upload files or prompts")
            json_data = {
                "patient_information": {
                    "age": None,
                    "symptoms": None,
                    "relevant_details": "No details to display. Please upload files or prompts"
                },
                "IMAGE_ANALYSIS": {
                    "image_type": "Empty image",
                    "image_analysis": "No image analysis to display. Please upload files or prompts"
                },
                "ans_to_ques": {"Answer": "Not applicable."},
                "differential_diagnosis": [],
                "alternative_diagnoses": [],
                "follow_up_recommendations": [],
                "biases": [
                    {"bias": "Lack of patient-specific information limits diagnostic accuracy.",
                     "recommendation": "Obtain a complete patient history, including age, symptoms,  and relevant medical background."},
                    {"bias": "Absence of medical examination data hinders comprehensive assessment.",
                     "recommendation": "Conduct a thorough physical examination and gather vital signs."},
                    {"bias": "Reliance on image data alone may lead to incomplete or inaccurate conclusions.",
                     "recommendation": "Integrate image findings with other diagnostic modalities, such as laboratory tests and clinical assessments."}
                ],
                "articles": [],
                "confidence_level": 10,
                "important_note": "This information is intended for informational and educational purposes only and does not constitute medical advice. It is essential to consult with a healthcare professional for any health concerns and should not be used as a substitute for a consultation with a healthcare provider."
            }
            st.session_state.json_data = json_data
        else:
            contents = [prompt]
            contents.extend([img[1] for img in images])

            response_text = call_gemini(contents, sys_ins)  # Get Raw Json
            json_data = parse_gemini_response(response_text)  # Parse to Json
            
            # Provide default JSON data if Gemini fails to return data
            if json_data is None:
               json_data = {
                   "patient_information": {
                       "age": None,
                       "symptoms": None,
                       "relevant_details": "No details to display because analysis failed. Ensure the file is correct and valid."
                   },
                   "IMAGE_ANALYSIS": {
                       "image_type": "Failed image",
                       "image_analysis": "Image analysis failed to upload. Ensure the file is correct and valid."
                   },
                   "ans_to_ques": {"Answer": "Not applicable."},
                   "differential_diagnosis": [],
                   "alternative_diagnoses": [],
                   "follow_up_recommendations": [],
                   "biases": [
                       {"bias": "Lack of patient-specific information limits diagnostic accuracy.",
                        "recommendation": "Obtain a complete patient history, including age, symptoms,  and relevant medical background."},
                       {"bias": "Absence of medical examination data hinders comprehensive assessment.",
                        "recommendation": "Conduct a thorough physical examination and gather vital signs."},
                       {"bias": "Reliance on image data alone may lead to incomplete or inaccurate conclusions.",
                        "recommendation": "Integrate image findings with other diagnostic modalities, such as laboratory tests and clinical assessments."}
                   ],
                   "articles": [],
                   "confidence_level": 10,
                   "important_note": "This information is intended for informational and educational purposes only and does not constitute medical advice. It is essential to consult with a healthcare professional for any health concerns and should not be used as a substitute for a consultation with a healthcare provider."
               }
            st.session_state.json_data = json_data

    # Display results *only if* json_data exists in session state
    if 'json_data' in st.session_state:
        display_results(st.session_state.json_data, images)

    # Place the "Show Follow-Up Recommendations" button *outside* the tabs
    if st.button("Show Follow-Up Recommendations"):
        st.session_state.show_followup = not st.session_state.show_followup

    # Conditionally display follow-up recommendations
    if st.session_state.get('show_followup', False) and 'json_data' in st.session_state:
        st.subheader("Follow-Up Recommendations")
        for recommendation in st.session_state.json_data.get('follow_up_recommendations', []):
            st.write(f"- {recommendation}")

    doctor_notes = st.text_area("Doctor's Notes", "")
    patient_name = st.text_input("Patient Name", "") # New prompt input
    doctor_signature = st.text_input("Doctor's Signature", "") # New prompt input

    # Generate PDF if Generate Diagnosis has been run
    if st.button("Generate PDF Report") and 'json_data' in st.session_state:
        now = datetime.now()
        formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
        # Access data from session_state
        json_data = st.session_state.json_data
        differential_diagnosis = json_data.get('differential_diagnosis', []) #Get it and make it safe
        
        # Determine primary diagnosis string
        primary_diagnosis_str = ""
        if differential_diagnosis and len(differential_diagnosis) > 0 : #check if it has differential diagnosis at all!
          primary_diagnosis_str = f"""
          <p><strong>Diagnosis:</strong> {differential_diagnosis[0].get('diagnosis', 'N/A') if differential_diagnosis[0] else 'N/A'}</p>
          <p><strong>Reasoning:</strong> {differential_diagnosis[0].get('reasoning', 'N/A') if differential_diagnosis[0] else 'N/A'}</p>
          <p><strong>Severity:</strong> {differential_diagnosis[0].get('severity', 'N/A') if differential_diagnosis[0] else 'N/A'}</p>
          <p><strong>Risk Factors:</strong> {differential_diagnosis[0].get('risk_factors', 'N/A') if differential_diagnosis[0] else 'N/A'}</p>
          """ #If its great add these elements
        else:
          primary_diagnosis_str = "<p>No diagnosis found.</p>" #If not do not add

        report_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
            body {{ font-family: Arial, sans-serif;
                    padding-top: 30px;  }} /* add padding to push content down */
            h1 {{ text-align: center; }}
            h2 {{ color: #333; }}
            p {{ line-height: 1.6; }}
            .section {{ margin-bottom: 20px; }}
            .contact-details {{ margin-top: 30px; text-align: center; }}
            .date-time {{ 
                text-align: right; 
                font-style: italic; 
                position: absolute;
                top: 5px;
                right: 5px;
                margin-top: -5px; /* pull the date-time up into the corner */
            }}
            </style>
            </head>
            <body>
            <div class="date-time">{formatted_date_time}</div>
            <h1>Medical Diagnosis Assistant Report</h1>

            <div class="section">
                <h2>Patient Information</h2>
                <p><strong>Patient Name:</strong> {patient_name if patient_name else "Not Specified"}</p>
                <p><strong>Age:</strong> {json_data.get('patient_information', {}).get('age', 'N/A')}</p>
                <p><strong>Symptoms:</strong> {json_data.get('patient_information', {}).get('symptoms', 'N/A')}</p>
            </div>

            <div class="section">
                <h2>Primary Diagnosis</h2>
                {primary_diagnosis_str} 
            </div>

            <div class="section">
                <h2>Image Analysis</h2>
                <p><strong>Image Type:</strong> {json_data.get('IMAGE_ANALYSIS', {}).get('image_type', 'N/A')}</p>
                <p><strong>Analysis:</strong> {json_data.get('IMAGE_ANALYSIS', {}).get('image_analysis', 'N/A')}</p>
            </div>

            <div class="section">
                <h2>Doctor's Notes</h2>
                <p>{doctor_notes}</p>
            </div>

            <div class="section">
                <h2>Doctor's Signature</h2>
                <p>{doctor_signature}</p>
            </div>

             <div class="section">
                <h2>Articles</h2>
                <ul>
                    {"".join([f"<li>{article}</li>" for article in json_data.get('articles', [])])}
                </ul>
            </div>

            <div class="contact-details">
                <p>Contact Us: medassistant@example.com | 1-800-MED-AI-DOC</p>
            </div>
            </body>
            </html>
            """

        # Generate and offer PDF file download
        try:
            pdf_report = pdfkit.from_string(report_html, False)
            st.subheader("Your pdf is ready to download!")

            b64_pdf = base64.b64encode(pdf_report).decode('UTF-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)

            download_button_str = f"""
                <a href="data:application/octet-stream;base64,{b64_pdf}" download="report.pdf" class="button">Download PDF</a>
            """
            st.markdown(download_button_str, unsafe_allow_html=True)
        except Exception as e:
             st.error(f"An error occurred during PDF generation: {e}. Please make sure you have followed the instructions to properly install PDF kit and added it to the path, as well as ghost script."," ""Also make sure that differential diagnosis exists for a primary diagnosis. Please upload files or prompt such that it will create a primary diagnosis for it.")
    
    json_data = st.session_state.get("json_data", None) #Set it to none so that the data does not throw
    st.info("This tool is intended for educational and informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Consult a qualified healthcare provider for any health concerns.")   

if __name__ == "__main__":
    main()
