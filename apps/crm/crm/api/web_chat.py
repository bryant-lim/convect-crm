import frappe
from urllib.parse import urlparse
import fnmatch

@frappe.whitelist(allow_guest=True)
def capture_web_lead(name, email, mobile_no=None, company_name=None, source="web_chat", notes=None, secret_token=None):
	# 1. Bypass whitelist checks if a valid secret token is provided
	expected_token = frappe.conf.get("web_chat_secret_token")
	header_token = frappe.request.headers.get("X-Web-Chat-Secret-Token")
	provided_token = secret_token or header_token
	
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

	# 2. Prevent duplicate email leads
	existing_lead = frappe.db.exists("CRM Lead", {"email": email})
	if existing_lead:
		# If notes is provided, append it to the existing lead's notes anyway!
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

	# 3. Insert CRM Lead
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
	
	# 4. Insert Notes/Chat Summary as CRM Note under this Lead
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
