import gradio as gr
import requests
import pandas as pd
from supabase import create_client, Client

# --- 1. CREDENTIALS & ASSETS ---
SUPABASE_URL = "https://ncnpfxqzdajeqiqqiqym.supabase.co"
SUPABASE_KEY = "sb_publishable_r_7ioxU7NuaeasrupjQLCQ_wLUfw8Ip"
CSS_URL = "https://raw.githubusercontent.com/bucks96/aitp_mishtee/main/style.py"
LOGO_URL = "https://raw.githubusercontent.com/bucks96/aitp_mishtee/main/Gemini_Generated_Image_j2lwc4j2lwc4j2lw.png"

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch CSS
try:
    response = requests.get(CSS_URL)
    mishtee_css = response.text if response.status_code == 200 else ""
except Exception:
    mishtee_css = ""

# --- 2. BACKEND FUNCTIONS ---

def get_trending_collections():
    """Fetches top 4 best-selling products by quantity."""
    res = supabase.table("orders").select(
        "product_id, qty_kg, products(sweet_name, variant_type, price_per_kg)"
    ).execute()
    
    if not res.data:
        return pd.DataFrame(columns=["Product", "Variant", "Price", "Total Orders"])

    df = pd.DataFrame(res.data)
    df['Product'] = df['products'].apply(lambda x: x['sweet_name'])
    df['Variant'] = df['products'].apply(lambda x: x['variant_type'])
    df['Price'] = df['products'].apply(lambda x: x['price_per_kg'])
    
    trending = df.groupby(['Product', 'Variant', 'Price'])['qty_kg'].sum().reset_index()
    trending = trending.sort_values(by='qty_kg', ascending=False).head(4)
    return trending

def handle_login(phone_number):
    """Processes login, greets customer, and returns history."""
    # Validate Phone
    if not phone_number.startswith('9') or len(phone_number) != 10:
        return "Please enter a valid 10-digit number starting with 9.", pd.DataFrame(), pd.DataFrame()

    # Fetch Customer Name
    user_res = supabase.table("customers").select("full_name").eq("phone", phone_number).execute()
    
    if not user_res.data:
        return "Namaste! No account found with this number.", pd.DataFrame(), pd.DataFrame()
    
    customer_name = user_res.data[0]['full_name']
    greeting = f"### Namaste, {customer_name} ji! Great to see you again."

    # Fetch Orders
    order_res = supabase.table("orders").select(
        "order_date, order_id, qty_kg, status, products(sweet_name)"
    ).eq("cust_phone", phone_number).order("order_date", desc=True).execute()

    # Format History Table
    if order_res.data:
        flat_history = []
        for row in order_res.data:
            flat_history.append({
                "Date": row['order_date'],
                "Order ID": row['order_id'],
                "Items": row['products']['sweet_name'],
                "Status": row['status']
            })
        history_df = pd.DataFrame(flat_history)
    else:
        history_df = pd.DataFrame(columns=["Date", "Order ID", "Items", "Status"])

    # Fetch Trending for global update
    trending_df = get_trending_collections()
    
    return greeting, history_df, trending_df

# --- 3. GRADIO UI LAYOUT ---

with gr.Blocks(css=mishtee_css, title="MishTee-Magic") as demo:
    
    # Header Section
    with gr.Row():
        gr.HTML(f"""
            <div style='text-align: center; padding: 30px;'>
                <img src='{LOGO_URL}' alt='Logo' style='max-width: 280px; margin: auto;'>
                <h2 style='font-family: "Playfair Display", serif; color: #C06C5C; margin-top: 10px;'>
                    Purity and Health in Every Bite
                </h2>
            </div>
        """)

    # Welcome & Login Space
    with gr.Column(elem_id="login-container"):
        greeting_output = gr.Markdown("Enter your number to unlock the magic.", elem_id="greeting")
        with gr.Row():
            phone_input = gr.Textbox(
                label="Registered Mobile Number", 
                placeholder="91234 56789",
                lines=1
            )
            login_btn = gr.Button("ACCESS ACCOUNT")

    gr.HTML("<br>")

    # Data Tabs for a clean Minimalist look
    with gr.Tabs():
        with gr.TabItem("My Order History"):
            history_table = gr.Dataframe(
                headers=["Date", "Order ID", "Items", "Status"],
                interactive=False
            )
        
        with gr.TabItem("Trending Today"):
            trending_table = gr.Dataframe(
                headers=["Product", "Variant", "Price", "Total Orders"],
                interactive=False
            )

    # Footer
    gr.Markdown("<center><small>MishTee-Magic | A2 Milk & Organic Artisanal Sweets</small></center>")

    # Event Triggers
    login_btn.click(
        fn=handle_login,
        inputs=[phone_input],
        outputs=[greeting_output, history_table, trending_table]
    )

# Launch
if __name__ == "__main__":
    demo.launch()
