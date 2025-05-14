from ad import agent_response
import streamlit as st
import asyncio,os
from blob import get_pdf, download_pdf_from_blob
 
st.title("Invoice Manager")
st.markdown("Enter a prompt to fetch or analyse any invoice.")
 
user_input = st.text_area("📝 Your Prompt", placeholder="E.g., Analyse the invoice of TSMC from january.")
 
# if st.button("Submit Prompt"):
#     with st.spinner("Processing..."):
#         result = asyncio.run(invoice_agent(user_input))
#         st.write(result)
 
import requests

def call_agent_api(input_param):
    url = "https://invoicemanager3.azurewebsites.net/api/agent_call"
    
    # Define the payload (input parameter to be passed in the request)
    payload = {
        "input": input_param  # Add the input parameter here
    }
    
    # Send a POST request to the Azure Function API
    try:
        response = requests.post(url, json=payload)
        print(response.content)

        # Check if the response status code is 200 (OK)
        if response.status_code == 200:
            return response.content # Assuming the API returns JSON
        else:
            print(f"Error: {response.status_code} - {response.text}")
    
    except Exception as e:
        print(f"Error while calling the API: {str(e)}")

import re
 
def extract_pdf_path(text):
    # Match most common PDF path patterns, even when surrounded by quotes or other punctuation
    match = re.search(r'[\w\-/\\:.]+\.pdf', text, flags=re.IGNORECASE)
    return match.group(0) if match else None
 
 
if st.button("Submit Prompt"):
    with st.spinner("Processing..."):
        result = call_agent_api(user_input)
        print('agent response:', result)
        
        pdf_path = extract_pdf_path(str(result))

        print('pdf path:', pdf_path)
        
        if pdf_path:
            print('Downloading pdf')
            pdf_path = pdf_path.replace(r'\\', r'/')
            print('Replaced pdf path:', pdf_path)
            download_pdf_from_blob(pdf_path)
            pdf_path = r'downloaded_invoice.pdf'
        
        
 
        import base64
       
        if pdf_path and os.path.isfile(pdf_path):
            print('Displaying pdf')

            
            with open(pdf_path, "rb") as f:

                pdf_data = base64.b64encode(f.read()).decode('utf-8')
 
            st.download_button("Download PDF", pdf_data, file_name=os.path.basename(pdf_path))
            st.markdown("### PDF Preview")
            st.write(pdf_path)
 
            from streamlit.components.v1 import html
 
            pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_data}" width="800" height="800" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            markdown = result.decode('utf-8')
            st.markdown(markdown)

 