import frappe
import random

def create_mock_data():
    # 1. Generate Malaysian names, emails, and company names
    first_names = [
        "Ahmad", "Muhammad", "Tan", "Chong", "Lim", "Siti", "Nur", "Logeswaran", "Karthik", "Ravi",
        "Mohd", "Abdul", "Syazwan", "Wei Shen", "Ming Leong", "Nurul", "Izzah", "Aminah", "Sarah",
        "Jonathan", "Rachel", "Kamarul", "Farhan", "Hafiz", "Zainal", "Subramaniam", "Vigneswaran"
    ]
    
    last_names = [
        "Bin Abdullah", "Bin Ibrahim", "Wei", "Shen", "Leong", "Anak Aminah", "Izzah", "Ramasamy", 
        "Subramaniam", "Maju", "Teoh", "Chong", "Tan", "Lim", "Goh", "Ali", "Othman", "Rahman"
    ]
    
    companies = [
        "Syarikat Logistik Maju", "Wei Shen Tech Solutions", "Kedai Runcit Aminah & Anak-Anak",
        "Borneo Coffee Co.", "KL Catering Services", "Penang Digital Media", "Selat Malaka Trading",
        "Nasi Kandar Pelita Express", "Malaysia Cyber Security Solutions", "Petronas Dealer Subang",
        "Johor Palm Oil Traders", "Ipoh White Coffee Distributors", "Borneo Timber Co.",
        "Klang Valley Logistics", "Sunway Printing & Design", "Melaka Heritage Hotel",
        "Kuching Seafood Wholesalers", "Kota Kinabalu Eco-Tours", "Cyberjaya App Development Studio",
        "Damansara Financial Advisors"
    ]
    
    # Generate 45 Leads
    leads_data = []
    for i in range(45):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        company = random.choice(companies) + f" {random.choice(['Sdn Bhd', 'Trading', 'Enterprise', 'Services'])}"
        email = f"{fn.lower().replace(' ', '')}{i}@example.com.my"
        phone = f"+601{random.randint(1, 9)}{random.randint(1000000, 9999999)}"
        leads_data.append({
            "first_name": f"{fn} {ln}",
            "email": email,
            "phone": phone,
            "organization": company
        })
        
    # Fetch valid statuses dynamically from the database to prevent validation errors
    valid_lead_statuses = [d.name for d in frappe.get_all("CRM Lead Status")]
    default_lead_status = valid_lead_statuses[0] if valid_lead_statuses else "New"
    
    created_leads = []
    print("Generating Malaysian SME mock leads...")
    for idx, lead in enumerate(leads_data):
        if not frappe.db.exists("CRM Lead", {"email": lead["email"]}):
            # Distribute statuses
            status = valid_lead_statuses[idx % len(valid_lead_statuses)] if valid_lead_statuses else default_lead_status
            
            # Create Lead doc
            doc_data = {
                "doctype": "CRM Lead",
                "first_name": lead["first_name"],
                "email": lead["email"],
                "status": status,
                "organization": lead["organization"]
            }
            
            # Handle phone number field name dynamically (could be mobile_no, phone, etc.)
            meta = frappe.get_meta("CRM Lead")
            if meta.get_field("mobile_no"):
                doc_data["mobile_no"] = lead["phone"]
            elif meta.get_field("phone"):
                doc_data["phone"] = lead["phone"]
                
            doc = frappe.get_doc(doc_data)
            doc.insert(ignore_permissions=True)
            created_leads.append(doc.name)
            print(f" -> Created Lead: {lead['first_name']} ({lead['organization']})")
        else:
            existing_lead = frappe.get_all("CRM Lead", filters={"email": lead["email"]}, limit=1)
            if existing_lead:
                created_leads.append(existing_lead[0].name)
            print(f" -> Lead already exists: {lead['first_name']}")
            
    frappe.db.commit()

    # Generate 25 Deals
    print("Generating mock deals...")
    valid_deal_statuses = [d.name for d in frappe.get_all("CRM Deal Status")]
    default_deal_status = valid_deal_statuses[0] if valid_deal_statuses else "Open"
    
    for idx in range(min(25, len(created_leads))):
        lead_name = created_leads[idx]
        lead_doc = frappe.get_doc("CRM Lead", lead_name)
        deal_title = f"Project for {lead_doc.organization or lead_doc.first_name}"
        
        # Check if Deal already exists
        if not frappe.db.exists("CRM Deal", {"lead": lead_name}):
            status = valid_deal_statuses[idx % len(valid_deal_statuses)] if valid_deal_statuses else default_deal_status
            
            doc_data = {
                "doctype": "CRM Deal",
                "lead": lead_name,
                "amount": random.randint(5000, 150000),
                "currency": "MYR"
            }
            
            # Handle status/stage field dynamically
            meta = frappe.get_meta("CRM Deal")
            status_field = None
            for f in meta.fields:
                if f.fieldtype == "Link" and f.options == "CRM Deal Status":
                    status_field = f.fieldname
                    break
            if status_field:
                doc_data[status_field] = status
            else:
                doc_data["status"] = status

            # Handle title/deal_name dynamically
            if meta.get_field("title"):
                doc_data["title"] = deal_title
            elif meta.get_field("deal_name"):
                doc_data["deal_name"] = deal_title
            
            if meta.get_field("organization") and lead_doc.organization:
                doc_data["organization"] = lead_doc.organization
                
            doc = frappe.get_doc(doc_data)
            doc.insert(ignore_permissions=True)
            print(f" -> Created Deal: {deal_title} with value {doc_data['amount']} MYR")
            
    frappe.db.commit()
    print("Done populating mock data!")

if __name__ == "__main__":
    create_mock_data()
