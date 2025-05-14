import logging
import io
import fitz  # PyMuPDF
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from collections import defaultdict
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv()


def download_pdf_from_blob(path):
    account_url = "https://strajpandey9250031017659.blob.core.windows.net"
    default_credential = DefaultAzureCredential()

    #print(default_credential.get_token())

    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient(account_url, credential=default_credential)

    # Download the blob to a local file
    # Add 'DOWNLOAD' before the .txt extension so you can see both files in the data directory
    #download_file_path = os.path.join(local_path, str.replace(local_file_name ,'.txt', 'DOWNLOAD.txt'))
    container_client = blob_service_client.get_container_client(container='invoicemanager3') 

    with open(file=r'downloaded_invoice.pdf', mode="wb") as download_file:

        blob_stream = container_client.download_blob(path)
    # Read ALL bytes from the stream and write them to the file
        download_file.write(blob_stream.readall())

        logging.info("\nDownloading blob to Relative path\n\t" + r'downloaded_invoice.pdf')

def get_pdf_from_blob(path):
    account_url = "https://strajpandey9250031017659.blob.core.windows.net"
    default_credential = DefaultAzureCredential()

    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient(account_url, credential=default_credential)

    # Download the blob directly into memory (using a memory buffer)
    container_client = blob_service_client.get_container_client(container='invoicemanager3')

    blob_client = container_client.get_blob_client(path)
    blob_stream = blob_client.download_blob()

    # Create a memory buffer and store the blob data in memory
    pdf_data = io.BytesIO(blob_stream.readall())
    logging.info("Downloaded blob to memory successfully.")

    return pdf_data


def extract_structured_text_from_pdf_in_memory(pdf_data, y_tolerance=3):
    # Open the PDF from the in-memory stream using fitz (PyMuPDF)
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    all_pages_data = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        rows_dict = defaultdict(list)

        for block in blocks:
            if block["type"] == 0:  # text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        y = round(span["bbox"][1])  # top Y of span
                        text = span["text"].strip()
                        if not text:
                            continue
                        # Group rows using Y-coordinate, allow slight variation
                        assigned = False
                        for row_y in rows_dict:
                            if abs(row_y - y) <= y_tolerance:
                                rows_dict[row_y].append((span["bbox"][0], text))  # (X-position, text)
                                assigned = True
                                break
                        if not assigned:
                            rows_dict[y].append((span["bbox"][0], text))

        # Sort rows by Y, then sort items in each row by X
        structured_rows = []
        for y in sorted(rows_dict):
            row = sorted(rows_dict[y], key=lambda x: x[0])
            structured_rows.append([text for _, text in row])

        all_pages_data.append(structured_rows)

    doc.close()
    return str(all_pages_data)


def get_pdf(path):

    pdf_data = get_pdf_from_blob(path)  # Get the PDF data in memory
    structured_text = extract_structured_text_from_pdf_in_memory(pdf_data)  # Extract structured text

    return structured_text


def upload_pdf_to_blob(pdf_bytes, blob_name):
    try:
        # Set up the BlobServiceClient
        container = 'invoicemanager3'

        account_url = "https://strajpandey9250031017659.blob.core.windows.net"  # Your Storage Account URL
        default_credential = DefaultAzureCredential()  # Use DefaultAzureCredential for authentication
        
        # Create BlobServiceClient instance
        blob_service_client = BlobServiceClient(account_url, credential=default_credential)
        
        # Create a container client
        container_client = blob_service_client.get_container_client(container='invoicemanager3')
        
        # Create a BlobClient instance
        blob_client = container_client.get_blob_client(blob_name)

        stream = io.BytesIO(pdf_bytes)
        blob_client.upload_blob(stream, overwrite=True)
        
        # Open the PDF file and upload it to Azure Blob Storage
        # Set overwrite to True to replace existing blob if any
        logging.info(f"PDF uploaded to container '{container}' as blob '{blob_name}'.")
            
        print(f"PDF uploaded to container '{container}' as blob '{blob_name}'.")
    
    except Exception as e:
        print(f"Error uploading file: {e}")


def list_all_blobs():

    container = 'invoicemanager3'

    account_url = "https://strajpandey9250031017659.blob.core.windows.net"  # Your Storage Account URL
    default_credential = DefaultAzureCredential()  # Use DefaultAzureCredential for authentication
    
    # Create BlobServiceClient instance
    blob_service_client = BlobServiceClient(account_url, credential=default_credential)
    
    # Create a container client
    container_client = blob_service_client.get_container_client(container='invoicemanager3')

    blobs = container_client.list_blobs()
        
    print(f"\nBlobs in container '{container}':")
    for blob in blobs:
        print(f" - {blob.name}")




if __name__ == '__main__':
    list_all_blobs()

    #download_pdf_from_blob(f'')
    pass
    #upload_pdf_to_blob('Youtube_2025-05-09.pdf','static\Invoices\Youtube\may\Youtube_2025-05-09.pdf' )






