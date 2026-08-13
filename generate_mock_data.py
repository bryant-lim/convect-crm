import frappe
import random
import datetime

def create_dummy_note(ref_doctype, ref_docname, title, content):
    note = frappe.get_doc({
        "doctype": "FCRM Note",
        "title": title,
        "content": f"<p>{content}</p>",
        "reference_doctype": ref_doctype,
        "reference_docname": ref_docname
    })
    note.insert(ignore_permissions=True)

def create_dummy_task(ref_doctype, ref_docname, title, description, priority="Medium"):
    due_date = datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 14), hours=random.randint(0, 23))
    task = frappe.get_doc({
        "doctype": "CRM Task",
        "title": title,
        "priority": priority,
        "status": random.choice(["Todo", "In Progress"]),
        "reference_doctype": ref_doctype,
        "reference_docname": ref_docname,
        "due_date": due_date.strftime("%Y-%m-%d %H:%M:%S"),
        "description": f"<p>{description}</p>"
    })
    task.insert(ignore_permissions=True)

def create_mock_data():
    # 0. Clean up old data to ensure clean, non-duplicated lists
    print("Cleaning up old data...")
    frappe.db.sql("DELETE FROM `tabCRM Lead`")
    frappe.db.sql("DELETE FROM `tabCRM Deal`")
    frappe.db.sql("DELETE FROM `tabCRM Task`")
    frappe.db.sql("DELETE FROM `tabFCRM Note`")
    frappe.db.sql("DELETE FROM `tabCRM Organization`")
    frappe.db.sql("DELETE FROM `tabContact`")
    frappe.db.sql("DELETE FROM `tabContact Email`")
    frappe.db.sql("DELETE FROM `tabContact Phone`")
    frappe.db.sql("DELETE FROM `tabCRM Contacts`")
    frappe.db.sql("DELETE FROM `tabDynamic Link` WHERE link_doctype IN ('CRM Lead', 'CRM Deal', 'CRM Organization')")
    frappe.clear_cache()
    frappe.db.commit()

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
    print("Generating Malaysian SME mock leads, contacts, and organizations...")
    for idx, lead in enumerate(leads_data):
        status = valid_lead_statuses[idx % len(valid_lead_statuses)] if valid_lead_statuses else default_lead_status
        
        # Create Lead doc with random annual revenue
        doc_data = {
            "doctype": "CRM Lead",
            "first_name": lead["first_name"],
            "email": lead["email"],
            "status": status,
            "organization": lead["organization"],
            "annual_revenue": random.randint(50000, 500000),
            "lead_owner": "Administrator"
        }
        if status in ["Junk", "Unqualified"]:
            doc_data["lost_reason"] = "Other"
            doc_data["lost_notes"] = "Not interested"
        
        # Handle phone number field name dynamically (could be mobile_no, phone, etc.)
        meta = frappe.get_meta("CRM Lead")
        if meta.get_field("mobile_no"):
            doc_data["mobile_no"] = lead["phone"]
        elif meta.get_field("phone"):
            doc_data["phone"] = lead["phone"]
            
        doc = frappe.get_doc(doc_data)
        doc.insert(ignore_permissions=True)
        
        # Sync Lead to generate Contact and CRM Organization records
        doc.create_organization()
        doc.create_contact(throw=False)
        
        # Add random tags to utilize tags features
        tags_pool = ["SME", "Hot", "VIP", "Cold", "Follow-up", "Logistics", "Tech"]
        selected_tags = random.sample(tags_pool, random.randint(1, 3))
        for tag in selected_tags:
            doc.add_tag(tag)
        
        created_leads.append(doc.name)
        
        # Generate dummy note for the Lead
        note_content = f"Spoke with {lead['first_name']} representing {lead['organization']}. Discussed logistics setup and potential requirements."
        create_dummy_note("CRM Lead", doc.name, "Initial Discussion Notes", note_content)

        # Generate dummy task for the Lead
        task_title = f"Follow up with {lead['first_name']}"
        task_desc = f"Send pricing details and standard service agreement for logistics integration."
        create_dummy_task("CRM Lead", doc.name, task_title, task_desc, priority=random.choice(["Low", "Medium", "High"]))

        print(f" -> Created Lead & Synced: {lead['first_name']} ({lead['organization']})")
            
    frappe.db.commit()

    # Generate 25 Deals
    print("Generating mock deals, notes, and tasks...")
    valid_deal_statuses = [d.name for d in frappe.get_all("CRM Deal Status")]
    default_deal_status = valid_deal_statuses[0] if valid_deal_statuses else "Open"
    
    for idx in range(min(25, len(created_leads))):
        lead_name = created_leads[idx]
        lead_doc = frappe.get_doc("CRM Lead", lead_name)
        deal_title = f"Project for {lead_doc.organization or lead_doc.first_name}"
        status = valid_deal_statuses[idx % len(valid_deal_statuses)] if valid_deal_statuses else default_deal_status
        
        # Populate Deals properly with values matching the associated Lead/Organization
        doc_data = {
            "doctype": "CRM Deal",
            "lead": lead_name,
            "deal_value": random.randint(5000, 150000),
            "expected_deal_value": random.randint(5000, 150000),
            "annual_revenue": lead_doc.annual_revenue or random.randint(50000, 500000),
            "organization": lead_doc.organization,
            "currency": "MYR",
            "deal_owner": "Administrator"
        }
        
        if status == "Lost":
            doc_data["lost_reason"] = "Other"
            doc_data["lost_notes"] = "Not interested"

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
            
        doc = frappe.get_doc(doc_data)
        
        # Find the synced Contact by email
        contact_name = frappe.db.get_value("Contact", {"email_id": lead_doc.email})
        if contact_name:
            contact_doc = frappe.get_doc("Contact", contact_name)
            doc.append("contacts", {
                "contact": contact_name,
                "full_name": contact_doc.full_name,
                "email": contact_doc.email_id,
                "phone": contact_doc.phone,
                "mobile_no": contact_doc.mobile_no,
                "is_primary": 1
            })
            
        doc.insert(ignore_permissions=True)

        # Generate dummy note for the Deal
        deal_note_content = f"Drafted logistics project proposal for {deal_title}. Standard MYR currency pricing applied."
        create_dummy_note("CRM Deal", doc.name, "Deal Proposal Draft", deal_note_content)

        # Generate dummy task for the Deal
        deal_task_title = f"Negotiate contract details for {deal_title}"
        deal_task_desc = f"Call client to finalize terms and secure approval of the proposal."
        create_dummy_task("CRM Deal", doc.name, deal_task_title, deal_task_desc, priority="High")

        print(f" -> Created Deal: {deal_title}")
            
    # Set default dashboard currency to MYR
    print("Setting default dashboard currency to MYR in FCRM Settings...")
    frappe.db.set_single_value("FCRM Settings", "currency", "MYR")

    # Disable telephony
    print("Disabling Twilio and Exotel integrations to hide calling buttons...")
    frappe.db.set_single_value("CRM Twilio Settings", "enabled", 0)
    frappe.db.set_single_value("CRM Exotel Settings", "enabled", 0)

    frappe.db.commit()
    print("Done populating mock data!")

if __name__ == "__main__":
    create_mock_data()
