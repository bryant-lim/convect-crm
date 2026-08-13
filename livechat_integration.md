# Live Chat CRM Integration Spec (Path B)

This document provides developers with the specifications and snippets required to sync user information from the website's Live Chat widget directly into Frappe CRM.

---

## 1. API Endpoint Details
* **Method**: `POST`
* **URL**: `https://crm.convect.tech/api/method/crm.api.web_chat.capture_web_lead`
* **Content-Type**: `application/json`
* **Authentication**: None required (secured via Origin/Referer whitelisting).

---

## 2. Request Parameters (JSON Body)

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | String | **Yes** | Visitor's full name (will be split automatically into first and last name by CRM). |
| `email` | String | **Yes** | Visitor's email address (CRM checks this to prevent duplicate leads). |
| `mobile_no` | String | No | Visitor's phone/mobile number. |
| `company_name` | String | No | Visitor's organization/company name (saves to CRM Lead's Organization field). |
| `source` | String | No | Source identifier (will default to `"web_chat"` if not passed). |
| `notes` | String | No | The chat summary or logs (saved as a CRM Note under the lead). |

---

## 3. Client JavaScript Code Snippet

```javascript
const leadData = {
    name: "John Doe",
    email: "john.doe@example.com",
    mobile_no: "+60123456789",
    company_name: "Creativa Studio",
    source: "web_chat",
    notes: "Visitor inquired about pricing plans and custom setups."
};

fetch('https://crm.convect.tech/api/method/crm.api.web_chat.capture_web_lead', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(leadData)
})
.then(response => response.json())
.then(data => {
    if (data.message && data.message.status === 'success') {
        console.log('Lead synced successfully. Lead ID:', data.message.lead);
    } else if (data.message && data.message.status === 'already_exists') {
        console.log('Lead already exists in CRM. Lead ID:', data.message.lead);
    } else {
        console.error('Failed to sync lead:', data);
    }
})
.catch(error => console.error('Connection error:', error));
```

---

## 4. Security / Domain Whitelist Warning
The CRM enforces strict CORS/Origin security checks. This request **must** originate from one of the following whitelisted domains configured in the CRM's `site_config.json`:
* `https://crm.convect.tech`
* `https://*.creativatestudio.my` (all subdomains)

If you attempt to call the endpoint from any other origin (including local development environments not listed in `site_config.json`), the CRM will reject the request with `403 Forbidden` (`PermissionError`).
