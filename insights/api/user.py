# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import split_emails, validate_email_address

from insights import notify


@frappe.whitelist()
def get_user_info():
    users = frappe.db.get_all(
        "User", fields=["name", "email", "user_image", "full_name", "user_type"]
    )
    out = {}
    for user in users:
        if frappe.session.user == user.name:
            user.session_user = True
        out[user.name] = user
    return out


@frappe.whitelist()
def add_insights_user(user):
    email_strings = validate_email_address(user.get("email"), throw=True)
    email_strings = split_emails(email_strings)
    if user.get("role") not in ["User", "Admin"]:
        frappe.throw("Invalid Role")

    doc = frappe.get_doc(
        {
            "doctype": "User",
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "email": email_strings[0],
            "user_type": "Website User",
            "send_welcome_email": 1,
        }
    )
    doc.append_roles(
        "Insights User" if user.get("role") == "User" else "Insights Admin"
    )
    doc.insert()
    frappe.db.commit()
    notify(
        type="success",
        title="User Added",
        message=f"{user.get('first_name')} {user.get('last_name')} has been added as an Insights {user.get('role')}",
    )

    if user.get("team"):
        try:
            team = frappe.get_doc("Insights Team", user.get("team"))
            team.append("team_members", {"user": doc.name})
            team.save()
        except frappe.DoesNotExistError:
            notify(
                type="error",
                title="Team Not Found",
                message=f"Team {user.get('team')} does not exist. Please create a new team or add the user to an existing team.",
            )
