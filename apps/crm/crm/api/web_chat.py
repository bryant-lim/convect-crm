import frappe
from urllib.parse import urlparse
import fnmatch

# Common aliases for field mapping
NAME_ALIASES = ["name", "full_name", "fullname", "visitor_name", "visitorname", "first_name"]
EMAIL_ALIASES = ["email", "email_id", "email_address", "emailaddress"]
MOBILE_ALIASES = ["mobile_no", "mobile", "phone", "phone_number", "phonenumber", "mobile_number", "contact"]
COMPANY_ALIASES = ["company_name", "companyname", "company", "organization", "org"]
NOTES_ALIASES = ["notes", "message", "enquiry", "msg", "comment", "enquiry_notes"]

# System keys to exclude from notes
SYSTEM_KEYS = ["source", "secret_token", "cmd"]

def get_field_by_aliases(payload, aliases, default=""):
	for alias in aliases:
		# Check case-insensitive key names and strip whitespaces/underscores
		for key, val in payload.items():
			if key.lower().replace(" ", "_").replace("-", "_") == alias.lower():
				return val
	return default

@frappe.whitelist(allow_guest=True)
def capture_web_lead(**kwargs):
	# Merge request arguments and body dictionary
	payload = frappe.form_dict.copy()
	
	# 1. Bypass whitelist checks if a valid secret token is provided
	expected_token = frappe.conf.get("web_chat_secret_token")
	header_token = frappe.request.headers.get("X-Web-Chat-Secret-Token")
	provided_token = payload.get("secret_token") or header_token
	
	is_authenticated = expected_token and provided_token == expected_token
	
	if not is_authenticated:
		# Enforce Origin/Referer whitelisting
		allowed_origins = frappe.conf.get("web_chat_allowed_origins") or []
		origin = frappe.request.headers.get("Origin")
		referer = frappe.request.headers.get("Referer")
		
		allowed_patterns = [urlparse(url).netloc for url in allowed_origins if url]
		
		request_domain = None
		if origin:
			request_domain = urlparse(origin).netloc
		elif referer:
			request_domain = urlparse(referer).netloc
			
		matched = False
		if request_domain:
			for pattern in allowed_patterns:
				if fnmatch.fnmatch(request_domain, pattern):
					matched = True
					break

		if not matched:
			frappe.throw(
				"Access Denied: Origin not whitelisted",
				frappe.PermissionError
			)

	# 2. Extract standard fields using case-insensitive alias matches
	name = get_field_by_aliases(payload, NAME_ALIASES, "Website Visitor")
	email = get_field_by_aliases(payload, EMAIL_ALIASES, "")
	mobile_no = get_field_by_aliases(payload, MOBILE_ALIASES, "")
	company_name = get_field_by_aliases(payload, COMPANY_ALIASES, "")
	notes = get_field_by_aliases(payload, NOTES_ALIASES, "")
	source = payload.get("source") or "web_chat"

	# 3. Capture any unmapped/extra fields (e.g. custom Google Form questions)
	extra_info = []
	all_mapped_aliases = NAME_ALIASES + EMAIL_ALIASES + MOBILE_ALIASES + COMPANY_ALIASES + NOTES_ALIASES + SYSTEM_KEYS
	
	for key, value in payload.items():
		normalized_key = key.lower().replace(" ", "_").replace("-", "_")
		if normalized_key not in all_mapped_aliases and value:
			extra_info.append(f"{key}: {value}")
			
	if extra_info:
		extra_notes_block = "\n".join(extra_info)
		notes = f"{notes}\n\nAdditional Details:\n{extra_notes_block}" if notes else extra_notes_block

	# 4. Prevent duplicate email leads
	if email:
		existing_lead = frappe.db.exists("CRM Lead", {"email": email})
		if existing_lead:
			if notes:
				note = frappe.get_doc({
					"doctype": "FCRM Note",
					"title": "Chat / Lead Summary",
					"content": f"New Enquiry summary:\n{notes}",
					"reference_doctype": "CRM Lead",
					"reference_docname": existing_lead
				})
				note.insert(ignore_permissions=True)
			return {"status": "already_exists", "lead": existing_lead}

	# Split full name into first and last name
	first_name = name.split(" ")[0] if name else "Website"
	last_name = " ".join(name.split(" ")[1:]) if name and len(name.split(" ")) > 1 else ""

	# 5. Insert CRM Lead
	lead = frappe.get_doc({
		"doctype": "CRM Lead",
		"first_name": first_name,
		"last_name": last_name,
		"email": email,
		"mobile_no": mobile_no or "",
		"organization": company_name or "",
		"source": source or "web_chat"
	})
	lead.insert(ignore_permissions=True)
	
	# 6. Insert Notes/Chat Summary as CRM Note under this Lead
	if notes:
		note = frappe.get_doc({
			"doctype": "FCRM Note",
			"title": "Chat / Lead Summary",
			"content": f"Enquiry summary:\n{notes}",
			"reference_doctype": "CRM Lead",
			"reference_docname": lead.name
		})
		note.insert(ignore_permissions=True)

	return {"status": "success", "lead": lead.name}
