from jinja2 import Template
import io
import pyodbc
import datetime
from xhtml2pdf import pisa
import datetime
import logging
from blob import upload_pdf_to_blob
  # Importing xhtml2pdf for PDF generation




def get_invoice_path_SQL(name: str, month: str) -> str:

    try:
        # Connect to the MySQL server
        conn_str = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:invoicemanager.database.windows.net,1433;Database=InvoiceManagerDB;Uid=rajpandey;Pwd={A!p2p3l4y5};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30'

        conn = pyodbc.connect(conn_str)
        
        cursor = conn.cursor()
        
        # SQL query to fetch product price from the 'product' table

        query = f"SELECT path, file_name FROM invoice_path WHERE LOWER(TRIM(CAST(name AS VARCHAR(255)))) = '{name.strip().lower()}'"
        cursor.execute(query)
        
        result = cursor.fetchone()  # Fetch the first result
        print(result[0]+ month + '/' + result[1])
        if result:
            return result[0]+ month + '/' + result[1] # Returning the price
        else:
            return None
        
    except Exception as e:
        logging.critical(f"Error getting invoice path: {e}")
        print(f"Error: {e}")
        return None

# Function to get product price from the database
def get_product_price(product_name):
    try:
        # Connect to the MySQL server
        conn_str = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:invoicemanager.database.windows.net,1433;Database=InvoiceManagerDB;Uid=rajpandey;Pwd={A!p2p3l4y5};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30'

        conn = pyodbc.connect(conn_str)
        
        cursor = conn.cursor()
        
        # SQL query to fetch product price from the 'product' table

        query = f"SELECT price FROM product_prices WHERE CAST(product AS VARCHAR(255)) = '{product_name}'"
        cursor.execute(query)
        
        result = cursor.fetchone()  # Fetch the first result
        print(result[0])
        if result:
            return result[0]  # Returning the price
        else:
            return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# Function to apply discount
def apply_discount(price, discount_percentage):
    discount_amount = (float(discount_percentage) / 100) * float(price)
    return float(price) - discount_amount

# Function to load the HTML template from a file
def load_html_template(template_path):
    with open(template_path, 'r') as file:
        return file.read()

# Function to generate the HTML invoice
def generate_html_invoice(invoice_data):
    
    customer = invoice_data["customer"]
    products = invoice_data["products"]

    # Load the HTML template from file
    html_template = load_html_template("invoice_template.html")

    # Create the template and render the HTML
    template = Template(html_template)

    # Get current date
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Calculate total amount based on discounts
    total = 0
    for product_name, discount_percentage in products.items():
        unit_price = get_product_price(product_name)
        if unit_price:
            discounted_price = apply_discount(unit_price, discount_percentage)
            total_price = discounted_price * 1  # Assuming quantity is 1
            total += total_price

    # Render the template with dynamic data
    html_content = template.render(
        customer=customer,
        current_date=current_date,
        products=products,
        get_product_price=get_product_price,
        apply_discount=apply_discount,
        total=total
    )

    return html_content

# Function to generate PDF from HTML using xhtml2pdf (Pisa)
def generate_pdf_from_html(invoice_data):
    # Generate the HTML invoice content
    customer = invoice_data["customer"]

    # SQL query to fetch product price from the 'product' table
    customer_safe = invoice_data["customer"].replace(" ", "_")
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f"{customer_safe}_{current_date}"

    current_date = datetime.datetime.now()
    current_month = current_date.strftime("%B").lower()
    output_pdf_path = f'static/Invoices/{customer}/{current_month}/{filename}.pdf'
   


    html_content = generate_html_invoice(invoice_data)
    pdf_buffer = io.BytesIO()

    # Create a PDF from HTML using xhtml2pdf
   

    pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
    if pisa_status.err:
        print("Error generating PDF")
    else:
        print(f"PDF generated successfully: {output_pdf_path}")
        conn_str = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:invoicemanager.database.windows.net,1433;Database=InvoiceManagerDB;Uid=rajpandey;Pwd={A!p2p3l4y5};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30'
        pdf_bytes = pdf_buffer.getvalue()
        upload_pdf_to_blob(pdf_bytes,output_pdf_path)


        conn = pyodbc.connect(conn_str)
        
        cursor = conn.cursor()
        
        

        folder_path = f"static/Invoices/{customer}/"
        
        cursor.execute(
                        """
                        INSERT INTO invoice_path (name, path, file_name)
                        VALUES (?, ?, ?)
                        """,
                        (customer, folder_path, filename)      # parameters tuple
                    )
        
        conn.commit()

        return output_pdf_path
    
        
if __name__ == "__main__":

    # invoice_data = {
    #             "customer": "Youtube",
    #             "products": {
    #                 "T-shirt": 15, 
    #                 "Sneakers": 50  
    #             }}


    # generate_pdf_from_html(invoice_data)

    conn_str = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:invoicemanager.database.windows.net,1433;Database=InvoiceManagerDB;Uid=rajpandey;Pwd={A!p2p3l4y5};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30'

    conn = pyodbc.connect(conn_str)
    
    cursor = conn.cursor()

    cursor.execute("DELETE FROM invoice_path")
    cursor.execute('''INSERT INTO invoice_path (name, path, file_name) VALUES
('USA Plastics', 'static/Invoices/USA_Plastics/', 'sample-invoice.pdf'),
('Infinix Steel', 'static/Invoices/Infinix/', 'sample-invoice.pdf'),
('Red Rubber Co.', 'static/Invoices/Red_Rubber/', 'sample-invoice.pdf'),
('TSMC', 'static/Invoices/TSMC/', 'sample-invoice.pdf');
 ''')
    cursor.execute('SELECT * FROM invoice_path')
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    cursor.commit()




#print(get_invoice_path('TSMC', 'january'))

# # Example usage
# invoice_data = {
#     "customer": "Youtube",
#     "products": {
#         "T-shirt": 15,  # 15% discount
#         "Sneakers": 50     # 50% discount
#     }
# }
# customer_safe = invoice_data["customer"].replace(" ", "_")
# current_date = datetime.datetime.now().strftime('%Y-%m-%d')
# filename = f"{customer_safe}_{current_date}.pdf"

# # Generate the invoice PDF
# generate_pdf_from_html(invoice_data, filename)

#get_product_price('T-shirt')








# import pyodbc

# # Set up the connection string
# conn_str = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:invoicemanager.database.windows.net,1433;Database=InvoiceManagerDB;Uid=rajpandey;Pwd={A!p2p3l4y5};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30'

# # Establish the connection
# conn = pyodbc.connect(conn_str)

# # # Create a cursor object using the connection
# cursor = conn.cursor()

# # # cursor.execute('''
# # # CREATE TABLE product_prices (
# # #     product TEXT,
# # #     price INT
# # # )
# # # ''')

# # # # Step 3: Insert the provided data into the table
# # # data = [
# # #     ("T-shirt", 499),
# # #     ("Jeans", 1299),
# # #     ("Sneakers", 2499),
# # #     ("Jacket", 1999),
# # #     ("Cap", 299),
# # #     ("Sunglasses", 899),
# # #     ("Backpack", 1499),
# # #     ("Watch", 3499),
# # #     ("Sweater", 1199),
# # #     ("Belt", 399)
# # # ]

# # # cursor.executemany('''
# # # INSERT INTO product_prices (product, price) VALUES (?, ?)
# # # ''', data)

# # # # Step 4: Commit the transaction to save the changes
# # # conn.commit()

# # Step 5: Fetch all rows (SELECT *)
#cursor.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'invoice_path';")

##Step 6: Print the results
# rows = cursor.fetchall()
# for row in rows:
#     print(row)

# # # cursor.execute("SELECT DB_NAME() AS CurrentDatabase")

# # # # Fetch the result
# # # current_db = cursor.fetchone()
# # print(f"Current database: {current_db.CurrentDatabase}")


# # Step 7: Close the connection
# cursor.close()
# conn.close()