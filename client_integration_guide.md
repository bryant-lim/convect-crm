# CRM Lead Sync API - Developer Integration Guide

This document describes how to integrate external web forms (e.g., custom website contact forms, landing page forms) or live chat widgets with the Frappe CRM Lead API.

---

## 1. Request Details

* **Endpoint**: `https://crm.convect.tech/api/method/crm.api.web_chat.capture_web_lead`
* **Method**: `POST`
* **Content-Type**: `application/json`

### Authentication & Security
The API checks domain origins to prevent unauthorized spam. However, for server-side requests (such as a Next.js/Node API route or Google Apps Script) or local testing, you should bypass the origin check by passing the secret token header:

* **Header Name**: `X-Web-Chat-Secret-Token`
* **Header Value**: `convect-token-secret-696`

*(Alternatively, you can pass `"secret_token": "convect-token-secret-696"` directly inside your JSON payload body).*

---

## 2. JSON Payload Schema

The API is designed to be highly flexible and will search your payload for standard field names using common aliases (case-insensitive, ignores spaces and dashes).

### Standard Fields
The following keys are mapped to standard fields inside the CRM Lead record:

| CRM Lead Field | Supported JSON Key Aliases | Description |
| :--- | :--- | :--- |
| **Name** | `name`, `full_name`, `fullname`, `visitor_name`, `first_name` | The contact's full name. Auto-splits into first and last names. |
| **Email** | `email`, `email_id`, `email_address`, `emailaddress` | The contact's email address. |
| **Mobile No** | `mobile_no`, `mobile`, `phone`, `phone_number`, `contact`, `tel` | The contact's phone number. |
| **Organization** | `company_name`, `company`, `organization`, `org` | The contact's company or organization. |
| **Notes** | `notes`, `message`, `enquiry`, `msg`, `comment` | Initial message or chat summary notes. |
| **Source** | `source` | Specifies the channel source (e.g., `"Google Form"`, `"Web Chat"`, `"Main Website"`). Defaults to `"web_chat"`. |

### Custom/Extra Fields
If your form collects extra fields (e.g. `"budget"`, `"timeline"`, `"services_needed"`), you can send them directly in the payload. The API will automatically gather all unrecognized keys and append them neatly under the Lead's **Enquiry Notes** section so no information is lost!

---

## 3. Integration Code Examples

### Example A: JavaScript (Fetch API)
```javascript
const payload = {
  name: "John Doe",
  email: "john@example.com",
  phone: "+60123456789",
  company: "Example Sdn Bhd",
  message: "Looking for custom CRM software.",
  // Custom fields (will be appended to lead notes automatically)
  budget: "RM5,000",
  timeline: "1 month",
  source: "Web Chat Widget"
};

fetch("https://crm.convect.tech/api/method/crm.api.web_chat.capture_web_lead", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-Web-Chat-Secret-Token": "convect-token-secret-696"
  },
  body: JSON.stringify(payload)
})
.then(response => response.json())
.then(data => console.log("Success:", data))
.catch(error => console.error("Error:", error));
```

### Example B: Shell / cURL
```bash
curl -X POST https://crm.convect.tech/api/method/crm.api.web_chat.capture_web_lead \
  -H "Content-Type: application/json" \
  -H "X-Web-Chat-Secret-Token: convect-token-secret-696" \
  -d '{
    "name": "Jane Smith",
    "email": "jane@example.com",
    "mobile": "+60171234567",
    "enquiry": "Interested in marketing service.",
    "source": "Landing Page"
  }'
```
