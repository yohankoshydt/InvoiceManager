import json
import datetime
import logging
from typing import Any, Callable, Set, Dict, List, Optional
from azdb import generate_pdf_from_html, get_invoice_path_SQL
from blob import get_pdf

d = 0

logging.basicConfig(level=logging.INFO)

def get_invoice_path(name: str, month: str) -> str:
    

    return get_invoice_path_SQL(name, month)
 

def interpret_pdf(pdf_path: str, system_prompt: str) -> str:
    
   
    from openai import AzureOpenAI
 
    client = AzureOpenAI(
        api_version="2024-12-01-preview",
        azure_endpoint="https://ai-rajpandey9762ai250031017659.services.ai.azure.com",
        api_key="2Rt9Euumib7ilO9yGwDZDOTIOKEpNFHwPNj8HJc3RiuWo6O5ldQvJQQJ99BEACHYHv6XJ3w3AAAAACOGmitj"
    )
    deployment = "gpt-4o"
    
    
    logging.debug(d)

    get_pdf(pdf_path)

    

    if not system_prompt:
        system_prompt = "You're a helpful assistant that understands and concisely explains the contents of invoices. Summarize this invoice."
   
    
 
    try:
        # Step 1: Extract text from the PDF

        text = get_pdf(pdf_path)
        logging.info(f'pdf content: {text}')
 
        if not text:
            logging.info( "No readable text found in the PDF.")
            return "No readable text found in the PDF."
 
        # Step 2: Send to OpenAI for interpretation

        response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": text,
            }
        ],
        max_completion_tokens=800,
        temperature=0.3,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        model=deployment
        )
 
        # with open("invoice_summary.txt", "w") as f:
        #     f.write(response.choices[0].message.content)

        return response.choices[0].message.content
 
    except FileNotFoundError:
        return f"File not found: {pdf_path}"
    except Exception as e:
        return f"Error interpreting PDF: {str(e)}"
    
    except Exception as e:
        return e
    


def create_invoice(invoice_data):

    path = generate_pdf_from_html(invoice_data)
    return path


def get_cat_name(colour):

    return "Sandra"

user_functions: Set[Callable[..., Any]] = {
    create_invoice, interpret_pdf, get_invoice_path
}


if __name__ == "__main__":
    # invoice_data = {
    #             "customer": "Youtube",
    #             "products": {
    #                 "T-shirt": 15,   
    #                 "Sneakers": 50   
    #             }
    #             }
    # create_invoice(invoice_data)

    p = get_invoice_path(name='TSMC', month='january')
    print(1,p)

    r = interpret_pdf('static\Invoices\TSMC\january\sample-invoice.pdf', 'What is the VAT in this pdf?')
    print(r)

