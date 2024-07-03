import streamlit as st
import plotly.express as px
import pandas as pd
import fitz  # PyMuPDF
import re
import plotly.graph_objects as go
import qrcode
from io import BytesIO
import plotly.express as px
from datetime import datetime, timedelta


st.set_page_config(page_title="Finance Management", page_icon=":bar_chart:", layout="wide")


# Define the function to extract text from all pages of a PDF
def extract_text_from_all_pages(pdf_path):
    document = fitz.open(pdf_path)
    all_text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text = page.get_text("text")
        all_text += text + "\n"  # Add a newline separator between pages
    return all_text

# Define the function to extract transactions from the text
def extract_transactions(text):
    pattern = re.compile(r"""
        (\d{2}/\d{2}/\d{4})\s+  # Posting Date
        (\d{2}/\d{2}/\d{4})\s+  # Transaction Date
        (.*?)                   # Everything else (description + money + balance)
        (?=\d{2}/\d{2}/\d{4}|End|$) # Look ahead for next date, "End", or end of string
    """, re.VERBOSE | re.DOTALL)

    transactions = []

    for match in pattern.finditer(text):
        posting_date, transaction_date, full_description = match.groups()

        # Split the full description into lines
        lines = full_description.strip().split('\n')

        # Skip this entry if there aren't at least two lines (for money and balance)
        if len(lines) < 2:
            continue

        # The last line is the balance
        balance = lines[-1].strip()

        # The second last line is money in/out
        money_value = lines[-2].strip()

        # Everything else is the actual description
        description = ' '.join(lines[:-2]).strip()

        # Try to convert money_value to float, skip if not possible
        try:
            float_value = float(money_value.replace(' ', '').replace(',', ''))
        except ValueError:
            continue  # Skip this entry if money_value can't be converted to float

        # Determine money in/out
        if float_value > 0:
            money_in = money_value
            money_out = "0.00"
        else:
            money_in = "0.00"
            money_out = money_value.lstrip('-')

        transactions.append({
            "Posting Date": posting_date,
            "Transaction Date": transaction_date,
            "Description": description,
            "Money In (R)": money_in,
            "Money Out (R)": money_out,
            "Balance (R)": balance
        })

    return transactions


#####################################################################################################################################################################
#Selecting different pages
pages = ["Financial Analysis", "Loyalty Cards"]
st.sidebar.header("Pages")
selected_page = st.sidebar.selectbox("Select Pages", pages)


if "Financial Analysis" in selected_page:
    
    st.title(":bar_chart: Finance System Trackers")
    st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)


    # File uploader widget
    fl = st.file_uploader(":file_folder: Upload a file", type=["pdf"])
    if fl is not None:
        filename = fl.name
        st.write(filename)
        
        with open(filename, "wb") as f:
            f.write(fl.getbuffer())
        
        # Extract text and transactions from the uploaded file
        text = extract_text_from_all_pages(filename)
        extracted_transactions = extract_transactions(text)
        
        # Create a DataFrame from the extracted transactions
        df = pd.DataFrame(extracted_transactions)
        
        #st.dataframe(df)
    else:
        # Example usage: Extract text from a sample PDF
        pdf_path = "C:/Users/Lusizo/Downloads/Manage finance account statement.pdf"
        text = extract_text_from_all_pages(pdf_path)
        extracted_transactions = extract_transactions(text)
        
        # Create a DataFrame from the extracted transactions
        df = pd.DataFrame(extracted_transactions)
        
        #st.dataframe(df)

    #####################  Data cleaning things ###############################################
    # Remove spaces and convert columns to appropriate data types
    df['Money In (R)'] = df['Money In (R)'].str.replace(' ', '').str.replace(',', '').astype(float)
    df['Money Out (R)'] = df['Money Out (R)'].str.replace(' ', '').str.replace(',', '').astype(float)
    df['Balance (R)'] = df['Balance (R)'].str.replace(' ', '').str.replace(',', '').astype(float)
    df['Description'] = df['Description'].astype(str)

    # Convert the "Transaction Date" column to a datetime format with the specified format
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='%d/%m/%Y')
    df['Posting Date'] = pd.to_datetime(df['Posting Date'], format='%d/%m/%Y') 

    #getting the min and max date
    startDate = pd.to_datetime(df["Transaction Date"]).min()
    endDate = pd.to_datetime(df["Transaction Date"]).max()
    
    #getting the min and max date
    startDate = pd.to_datetime(df["Transaction Date"]).min()
    endDate = pd.to_datetime(df["Transaction Date"]).max()


    #creating timeline to choosee from
    col1, col2 = st.columns(2)

    with col1:
        date1 = pd.to_datetime(st.date_input("Start Date", startDate))

    with col2:
        date2 = pd.to_datetime(st.date_input("End Date", endDate))

    #filtering the date
    df = df[(df["Transaction Date"]>= date1) & (df["Transaction Date"] <=date2)].copy ()

    #########################################################################################################################################################
    # Creating categories
    categories = {
        'Groceries': [
            'Checkers', 'Pick n Pay', 'Woolworths', 'Spar', 'Shoprite', 'Makro', 'Food Lover\'s Market', 'Game', 
            'Boxer', 'OK Foods', 'Usave', 'Cambridge Food', 'President Hyper'
        ],
        'Entertainment': [
            'Netflix', 'Spotify', 'Showmax', 'DSTV', 'Disney+', 'Apple TV', 'Amazon Prime Video', 'Hulu', 'Cinema',
            'Theatre', 'Concert', 'Event', 'Gaming', 'Xbox', 'PlayStation', 'Nintendo'
        ],
        'Transport': [
            'Uber', 'Bolt', 'Taxify', 'Taxi', 'Bus', 'MyCiTi', 'Gautrain', 'PRASA', 'Metrobus', 'Rea Vaya', 'Golden Arrow',
            'Flight', 'SA Express', 'Mango', 'Kulula', 'Lift', 'FlySafair', 'South African Airways', 'Car Rental', 'Avis',
            'Budget', 'Europcar', 'Hertz'
        ],
        'Household': [
            'Mr Price Home', 'Game', 'Makro', 'Builder\'s Warehouse', 'Checkers Hyper', 'HomeChoice', 'Woolworths Home',
            'Sheet Street', 'Pep Home', '@Home', 'Tupperware', 'Yuppiechef'
        ],
        'Medical': [
            'Clicks', 'Dis-Chem', 'Medirite', 'Pharmacy', 'Doctor', 'Dentist', 'Clinic', 'Hospital', 'Optometrist', 'Mediclinic',
            'Netcare', 'Life Healthcare', 'MediCross', 'Ampath', 'Lancet'
        ],
        'Personal & Family': [
            'Edgars', 'Foschini', 'Truworths', 'Woolworths', 'Mr Price', 'Ackermans', 'Pep', 'H&M', 'Zara', 'Cotton On', 
            'Sportsmans Warehouse', 'TotalSports', 'Cape Union Mart', 'Clicks', 'Dis-Chem'
        ],
        'Cash Withdrawal': [
            'ATM Withdrawal', 'Cash Withdrawal', 'Bank Withdrawal', 'Absa ATM', 'FNB ATM', 'Nedbank ATM', 'Standard Bank ATM',
            'Capitec ATM', 'TymeBank ATM', 'Bidvest ATM'
        ],
        'Communication': [
            'Vodacom', 'MTN', 'Telkom', 'Cell C', 'Rain', 'Afrihost', 'Webafrica', 'Internet', 'Data Bundle', 'Airtime',
            'Telkom Landline', 'VoIP', 'WiFi', 'Fiber', 'ISPs', 'ADSL'
        ],
        'Transfer': [
            'Bank Transfer', 'EFT', 'Wire Transfer', 'Interbank Transfer', 'Deposit', 'Withdrawal', 'Transaction',
            'Instant Money', 'Cash Send', 'MoneyGram', 'Western Union', 'PayPal', 'SnapScan', 'Zapper'
        ],
        'Alcohol': [
            'Liquor Store', 'Bottle Store', 'Tops', 'Checkers Liquor', 'Pick n Pay Liquor', 'Makro Liquor', 'Ultra Liquors',
            'Liquor City', 'Cape Wine', 'Beerhouse', 'Wine Shop', 'Distillery'
        ],
        'Restaurants': [
            'Restaurant', 'Cafe', 'Bistro', 'Diner', 'Steakhouse', 'Sushi Bar', 'Pizzeria', 'Fast Food', 'KFC', 'McDonald\'s',
            'Burger King', 'Nando\'s', 'Wimpy', 'Spur', 'Rocomamas', 'Ocean Basket', 'Mugg & Bean', 'Steers', 'Debonairs', 'Food', 'Chips'
        ],
        'Going Out': [
            'Bar', 'Pub', 'Club', 'Nightclub', 'Lounge', 'Party', 'Event', 'Festival', 'Live Music', 'DJ', 'Karaoke', 'Happy Hour'
        ],
        'Courier & Delivery': [
            'Droppa', 'Buffalo Logistics', 'Paxi', 'The Courier Guy', 'Courier', 'Delivery', 'Parcel', 'Package', 'Aramex', 
            'DHL', 'FedEx', 'UPS', 'PostNet', 'Fastway Couriers', 'RAM'
        ],
        'Online Stores': [
            'Amazon', 'Shein', 'Temu', 'eBay', 'Alibaba', 'Takealot', 'Superbalist', 'Zando', 'Wish', 'ASOS', 'Mr Price Online', 
            'Woolworths Online', 'Pick n Pay Online', 'Checkers Sixty60'
        ],
        'Education': [
            'University', 'College', 'Online Course', 'Uwc','UNISA', 'Wits', 'UCT', 'Stellenbosch', 'UP', 'UJ', 'UKZN', 'NWU',
            'Coursera', 'edX', 'Udemy', 'FutureLearn', 'GetSmarter'
        ],
        'Fuel': [
            'Petrol Station', 'Garage', 'Diesel Station', 'Shell', 'BP', 'Engen', 'Caltex', 'Total', 'Sasol'
        ],
        'Health and Fitness': [
            'Gym', 'Marathon', 'Virgin Active', 'Planet Fitness', 'Zone Fitness', 'Curves', 'CrossFit', 'Yoga Studio',
            'Pilates', 'Two Oceans Marathon', 'Comrades Marathon', 'Cape Town Cycle Tour', 'Parkrun', 'Sport', "Fitness"
        ],
        'Utilities': [
            'Electricity', 'Water', 'Rent', 'Levies', 'Eskom', 'Municipal Bill', 'City of Cape Town', 'City Power',
            'Johannesburg Water', 'Body Corporate'
        ],
        'Insurance': [
            'Car Insurance', 'Life Insurance', 'Home Insurance', 'Discovery Insure', 'OUTsurance', 'Santam', 'MiWay',
            'Budget Insurance', 'Hollard', 'Old Mutual Insure'
        ],
        'Investments': [
            'Stocks', 'Mutual Funds', 'Retirement Accounts', 'ETF', 'Unit Trust', 'Old Mutual', 'Coronation',
            'Allan Gray', 'Sygnia', 'Satrix', 'Easy Equities'
        ],
        'Travel': [
            'Hotels', 'Airlines', 'Travel Agencies', 'Airbnb', 'Booking.com', 'Expedia', 'Flight Centre',
            'Thompsons Holidays', 'Travelstart', 'Tripadvisor'
        ],
        'Home Services': [
            'Plumbing', 'Electrician', 'Cleaning Services', 'Handyman', 'Gardening Services', 'Pest Control',
            'Painting Services', 'Home Repairs'
        ],
        'Beauty and Personal Care': [
            'Salon', 'Spa', 'Barber Shop', 'Sorbet', 'Clicks Beauty', 'Dis-Chem Beauty', 'Dream Nails',
            'Skin Renewal', 'Massage', 'Waxing'
        ],
        'Pet Care': [
            'Veterinarian', 'Pet Store', 'Pet Grooming', 'Pets at Home', 'Absolute Pets', 'Montego Pet Nutrition',
            'Vet', 'Doggobone', 'Cat','Dog'
        ],
        'Electronics': [
            'Incredible Connection', 'Dion Wired', 'Makro Electronics', 'Game Electronics', 'Hi-Fi Corp',
            'Takealot Electronics', 'iStore', 'Vodacom Shop', 'MTN Store', 'Samsung Store'
        ],
        'Income': 
        ['Salary', 'Wages', 'Payroll', 'Deposit', 'Earnings', 'Compensation', 'Stipend', 'Bursary']
    }

    # Function to categorize transactions
    def categorize_transaction(description):
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword.lower() in description.lower():
                    return category, keyword  # Return both category and specific product/service
        return 'Other', 'Other'  # Default return if no match found

    # Apply categorization
    df["Category"], df["Product/Service"] = zip(*df["Description"].apply(categorize_transaction))

    #####################################################################################################################################################################

    # Sidebar filter options for categories
    st.sidebar.header("Choose your filter:")
    selected_categories = st.sidebar.multiselect("Pick a category", df["Category"].unique())

    # If no categories are selected, include all categories
    if not selected_categories:
        df_category_filtered = df.copy()
    else:
        df_category_filtered = df[df["Category"].isin(selected_categories)]

    # Sidebar filter options for product/services based on selected categories
    st.sidebar.header("Choose your filter:")
    selected_items = st.sidebar.multiselect("Pick a product/item/service", df_category_filtered["Product/Service"].unique())

    # If no product/services are selected, include all product/services
    if not selected_items:
        df_item_filtered = df_category_filtered.copy()
    else:
        df_item_filtered = df_category_filtered[df_category_filtered["Product/Service"].isin(selected_items)]

    # Display the filtered DataFrame based on selected categories and product/services
    if not selected_categories and not selected_items:
        filtered_df = df  # Show the original DataFrame if no filters are applied
    elif not selected_items:
        filtered_df = df[df["Category"].isin(selected_categories)]  # Filter by selected categories only
    else:
        # Filter by both selected categories and product/services
        filtered_df = df_item_filtered[df_item_filtered["Category"].isin(selected_categories) & df_item_filtered["Product/Service"].isin(selected_items)]


    # Calculate total Money In and Money Out
    df_category_total_money_in = filtered_df.groupby('Category')['Money In (R)'].sum()
    df_category_total_money_out = filtered_df.groupby('Category')['Money Out (R)'].sum()

    # Aggregate the data by category
    category_totals = filtered_df.groupby('Category')['Money Out (R)'].sum().reset_index()


    max_value_out = category_totals['Money Out (R)'].max()
    min_value_out = category_totals['Money Out (R)'].min()

    with col1:
        st.subheader("Category Expenses")
        fig = px.bar(
            category_totals,
            x='Category',
            y='Money Out (R)',
            text='Money Out (R)',
            color='Category',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            template='plotly_white'
        )
        fig.update_traces(
            texttemplate='R%{text:.2f}',
            textposition='outside',
            cliponaxis=False
        )
        fig.update_layout(
            xaxis_title="",
            yaxis_title="Total Money Out (R)",
            bargap=0.2,
            height=500,
            uniformtext_minsize=8,
            uniformtext_mode='hide',
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Items and Services Money Spent")
        fig = px.pie(filtered_df, values='Money Out (R)', names='Product/Service', hole=0.5)
        fig.update_traces(text = filtered_df["Product/Service"], textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    ################################################################################################################################################################################
    # Display the results using plotly charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Category Expenses")
        Category_ViewData = st.expander("Category View Data")
        # Convert Series to DataFrame and reset index
        df_category_total_money_out_df = df_category_total_money_out.reset_index()
        df_category_total_money_out_df.columns = ['Category', 'Money Out (R)']
        # Display as a regular dataframe
        Category_ViewData.dataframe(df_category_total_money_out_df)
        csv_category = df_category_total_money_out_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Data", data=csv_category, file_name="Category.csv", mime="text/csv", help="Click here to download the data as a CSV file")

    with col2:
        st.subheader("Items and Services Money Spent")
        Items_and_Services_ViewData = st.expander("Items and Services View Data")
        items_and_services = filtered_df.groupby(by='Product/Service', as_index=False)["Money Out (R)"].sum()
        # Display as a regular dataframe
        Items_and_Services_ViewData.dataframe(items_and_services)
        csv_items = items_and_services.to_csv(index=False).encode('utf-8')
        st.download_button("Download Data", data=csv_items, file_name="Items_and_Services.csv", mime="text/csv", help="Click here to download the data as a CSV file")

    #############################################################################################################################################################################
    # Calculate total expenses
    total_expenses = filtered_df['Money Out (R)'].sum()
    total_income = filtered_df['Money In (R)'].sum()

    # Create month-year column
    filtered_df["month_year"] = filtered_df["Transaction Date"].dt.to_period("M")

    # Create a layout with two columns
    col1, col2 = st.columns([3, 1])

    # Place the header in the left column
    with col1:
        st.subheader("Time Series Analysis")

    # Group by month-year and sum the 'Money Out (R)' column
    linechart = filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y-%m"))["Money Out (R)"].sum().reset_index()

    # Sort the dataframe by date
    linechart = linechart.sort_values("month_year")

    # Create the line chart
    fig2 = px.line(
        linechart,
        x="month_year",
        y="Money Out (R)",
        labels={"month_year": "Month-Year", "Money Out (R)": "Total Expenses (R)"},
        height=500,
        width=1000,
        template="plotly_white"
    )

    # Customize the layout
    fig2.update_layout(
        xaxis_title="Date",
        yaxis_title="Total Expenses (R)",
        xaxis=dict(tickangle=45),
        yaxis=dict(tickprefix="R", tickformat=",.0f"),
        hovermode="x unified"
    )

    # Add markers to the line
    fig2.update_traces(mode="lines+markers")

    ############################################################   Displaying income time series on the same chart      ################################
    # Calculate net income (income - expenses)
    net_income = total_income - total_expenses

    with col2:
        # Add checkbox for income comparison
        show_income = st.checkbox("Compare with Income")

    if show_income:
        income_chart = filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y-%m"))["Money In (R)"].sum().reset_index()
        income_chart = income_chart.sort_values("month_year")

        # Add income line to the existing chart
        fig2.add_trace(go.Scatter(
            x=income_chart["month_year"],
            y=income_chart["Money In (R)"],
            mode="lines+markers",
            name="Income"
        ))

        # Update layout for dual axis if needed
        fig2.update_layout(
            yaxis=dict(title="Amount (R)", tickprefix="R", tickformat=",.0f"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        # Display the chart
        st.plotly_chart(fig2, use_container_width=True)

        # Display total expenses and income
        st.markdown(f"**Total expenses from {date1.strftime('%d %B %Y')} to {date2.strftime('%d %B %Y')}: R{total_expenses:,.2f}**")
        st.markdown(f"**Total income from {date1.strftime('%d %B %Y')} to {date2.strftime('%d %B %Y')}: R{total_income:,.2f}**")
    else:
        # Display the chart
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown(f"**Total expenses from {date1.strftime('%d %B %Y')} to {date2.strftime('%d %B %Y')}: R{total_expenses:,.2f}**")

    # Display net income with color coding
    if net_income >= 0:
        st.markdown(f"**Net income: <span style='color:green'>R{net_income:,.2f}</span>**", unsafe_allow_html=True)
    else:
        st.markdown(f"**Net income: <span style='color:red'>R{net_income:,.2f}</span>**", unsafe_allow_html=True)

    #####################################################################################################################################################
    with st.expander("View Data of Time Series: "):
        st.write(linechart.T.style.background_gradient(cmap="Blues"))
        csv_timeSeries = linechart.to_csv(index=False).encode("utf-8")
        st.download_button("Download Data", data=csv_timeSeries, file_name="TimeSeries.csv", mime='text/csv')

    #####################################################################################################################################################
    # Calculate average monthly expense
    num_months = len(linechart)
    avg_monthly_expense = total_expenses / num_months if num_months > 0 else 0

    # Find the month with highest expense
    max_expense_month = linechart.loc[linechart['Money Out (R)'].idxmax()]

    # Generate recommendations
    st.subheader("Financial Insights")

    st.write(f"1. Your average monthly expense is R{avg_monthly_expense:,.2f}.")

    st.write(f"2. The month with the highest expenses was {max_expense_month['month_year']} "
             f"with total expenses of R{max_expense_month['Money Out (R)']:,.2f}.")

    if avg_monthly_expense > 0:
        highest_categories = filtered_df.groupby('Category')['Money Out (R)'].sum().nlargest(3)
        highest_items = df_item_filtered.groupby("Product/Service")['Money Out (R)'].sum().nlargest(3)
        
        # Display the filtered DataFrame based on selected categories and product/services
        if not selected_categories and not selected_items:
            filtered_df = df  # Show the original DataFrame if no filters are applied
            st.write("3. Your top 3 expense categories are:")
            for category, amount in highest_categories.items():
                st.write(f"   - {category}: R{amount:,.2f}")
        elif not selected_items:
             st.write("3. Your top 3 expense Items and Services are:")
             for item, amount in highest_items.items():
                st.write(f"   -   {item}: R{amount:,.2f}")
                
if "Loyalty Cards" in selected_page:
    # Function to load loyalty cards from a CSV file
    def load_loyalty_cards():
        try:
            return pd.read_csv('loyalty_cards.csv')
        except FileNotFoundError:
            return pd.DataFrame(columns=['Card Name', 'Card Number', 'Expiry Date'])

    # Function to save loyalty cards to a CSV file
    def save_loyalty_cards(cards_df):
        cards_df.to_csv('loyalty_cards.csv', index=False)

    # Function to generate QR code
    def generate_qr_code(data):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return buffered.getvalue()

    # Load existing loyalty cards
    loyalty_cards_df = load_loyalty_cards()

    st.title("Loyalty Card Management")

    # Add new loyalty card
    with st.expander("Add New Loyalty Card"):
        card_name = st.text_input("Card Name")
        card_number = st.text_input("Card Number")
        expiry_date = st.date_input("Expiry Date")
        if card_name.strip() == '' or card_number.strip() == '' or expiry_date.strip() == '':
            st.error("Please enter both Card Name and Card Number.")
        
        if st.button("Add Card"):
            new_card = pd.DataFrame({
                'Card Name': [card_name],
                'Card Number': [card_number],
                'Expiry Date': [expiry_date]
            })
            loyalty_cards_df = pd.concat([loyalty_cards_df, new_card], ignore_index=True)
            save_loyalty_cards(loyalty_cards_df)
            st.success("Card added successfully!")

    # Display and manage existing cards
    for index, card in loyalty_cards_df.iterrows():
        with st.expander(f"Card: {card['Card Name']}"):
            st.write(f"Card Number: {card['Card Number']}")
            st.write(f"Expiry Date: {card['Expiry Date']}")
            
            # Generate and display QR code
            qr_code = generate_qr_code(card['Card Number'])
            st.image(qr_code, caption=f"QR Code for {card['Card Name']}")
            
            # Option to delete card
            if st.button("Delete Card", key=f"delete_{index}"):
                loyalty_cards_df = loyalty_cards_df.drop(index)
                save_loyalty_cards(loyalty_cards_df)
                st.success("Card deleted successfully!")
                st.experimental_rerun()

    # Display all cards in a table
    st.subheader("All Loyalty Cards")
    st.dataframe(loyalty_cards_df)
    
    

def load_goals():
    try:
        return pd.read_csv('financial_goals.csv', parse_dates=['Deadline'])
    except FileNotFoundError:
        return pd.DataFrame(columns=['Name', 'Target Amount', 'Deadline', 'Current Amount', 'Status', 'Category'])

def save_goals(goals_df):
    goals_df.to_csv('financial_goals.csv', index=False)
    
    
if __name__ == "__main__":
    import os
    from streamlit.web import cli as stcli
    os.system("streamlit run app.py")
