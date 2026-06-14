import os
from datetime import datetime
import pandas as pd
import requests  # Run: pip install requests

print("🚀 Launching ServiceNow Shift Auto-Assignment Engine...")

# Configuration
roster_file = "C:/devhome/projects/shift_roster.xlsx"
instance_url = "https://your_barclays_instance.service-now.com/api/now/table/incident"
assignment_group_id = "YOUR_ASSIGNMENT_GROUP_SYS_ID"  # Replace with your team's group ID

# Barclays Inbound API Headers
headers = {"Content-Type": "application/json", "Accept": "application/json"}
auth = ("your_api_username", "your_api_password")  # Secure with system account credentials


def get_current_shift():
    """Determines the active shift window based on the current hour (24hr clock)"""
    current_hour = datetime.now().hour

    if 6 <= current_hour < 14:  # 06:00 to 14:00
        return "APAC"
    elif 14 <= current_hour < 22:  # 14:00 to 22:00
        return "EMEA"
    else:  # 22:00 to 06:00
        return "AMER"


try:
    # 1. Determine active shift and get engineers from Excel roster
    active_shift = get_current_shift()
    print(f"⏰ Current Active Shift: {active_shift}")

    df = pd.read_excel(roster_file)
    shift_data = df[df["Shift"].str.upper() == active_shift]

    if shift_data.empty:
        raise ValueError(f"No engineers configured in Excel for shift: {active_shift}")

    # Create an array of active engineers for this shift
    engineersOnShift = [
        shift_data.iloc[0]["Primary_Engineer"],
        shift_data.iloc[0]["Secondary_Engineer"],
    ]
    # Filter out any blank slots
    engineersOnShift = [eng for eng in engineersOnShift if pd.notna(eng)]
    print(f"👥 Active Roster on Shift: {engineersOnShift}")

    # 2. Fetch unassigned incidents belonging to your group from ServiceNow
    # Query details: group matching yours AND assigned_to is empty AND ticket is active
    query = f"assignment_group={assignment_group_id}^assigned_toISEMPTY^active=true"
    get_url = f"{instance_url}?sysparm_query={query}&sysparm_fields=sys_id,number,short_description"

    response = requests.get(get_url, auth=auth, headers=headers)

    if response.status_code != 200:
        raise ConnectionError(f"ServiceNow API connection failed: {response.text}")

    unassigned_tickets = response.json().get("result", [])
    print(f"📥 Found {len(unassigned_tickets)} unassigned tickets in the queue.")

    # 3. Round-Robin Assignment Rotation
    if len(unassigned_tickets) > 0 and len(engineersOnShift) > 0:
        engineer_index = 0

        for ticket in unassigned_tickets:
            ticket_sys_id = ticket["sys_id"]
            ticket_number = ticket["number"]
            # Pick the next engineer in the list
            assigned_engineer = engineersOnShift[engineer_index]

            print(f"🔄 Allocating {ticket_number} -> {assigned_engineer}")

            # Fire the PATCH update to ServiceNow to assign the user
            patch_url = f"{instance_url}/{ticket_sys_id}"
            payload = {
                "assigned_to": assigned_engineer,
                "work_notes": f"🤖 [Shift Automation] Ticket automatically allocated to {assigned_engineer} during the {active_shift} shift.",
            }

            patch_response = requests.patch(
                patch_url, auth=auth, headers=headers, json=payload
            )

            if patch_response.status_code == 200:
                print(f"✅ Successfully assigned {ticket_number}!")
            else:
                print(f"❌ Failed to assign {ticket_number}: {patch_response.text}")

            # Cycle to the next engineer in the roster array cleanly
            engineer_index = (engineer_index + 1) % len(engineersOnShift)

        print("🎉 Queue allocation sweep completed successfully!")
    else:
        print("☕ Queue is clean. No allocation movements needed right now.")

except Exception as e:
    print(f"Execution failed: {e}")