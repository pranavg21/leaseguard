"""Synthetic sample evidence for a deposit dispute, matching the sample agreement.

Every name, number and message here is invented for demonstration.
"""

SAMPLE_EVIDENCE: dict[str, str] = {
    "whatsapp_chat_with_landlord.txt": (
        "01/10/2025, 09:30 - Priya Nair: Hi Ravi ji, I have transferred the security deposit today.\n"
        "01/10/2025, 09:41 - Ravi Sharma: Received, thank you. Welcome to the flat!\n"
        "31/08/2026, 18:05 - Priya Nair: I have vacated the flat and handed over the keys to your manager today.\n"
        "02/09/2026, 11:12 - Ravi Sharma: Keys received. Flat is fine. I will return your full deposit within 7 days.\n"
        "15/09/2026, 20:47 - Ravi Sharma: I am deducting Rs. 60,000 for painting charges and cleaning.\n"
        "the balance will come later\n"
        "16/09/2026, 08:15 - Priya Nair: Please refund the deposit as promised. There was no damage.\n"
    ),
    "upi_receipt_deposit.txt": (
        "UPI Payment Receipt\n"
        "Date: 01/10/2025\n"
        "Paid Rs. 2,50,000 to Ravi Sharma towards security deposit for Flat 4, Baner, Pune\n"
        "UPI Ref No. 5213009877\n"
        "Status: SUCCESS\n"
    ),
    "email_refund_request.txt": (
        "From: Priya Nair\n"
        "To: Ravi Sharma\n"
        "Date: 20 September 2026\n"
        "Subject: Refund of security deposit\n"
        "This is a reminder that the full deposit of Rs. 2,50,000 is still pending.\n"
        "I request you to refund the deposit within 7 days.\n"
    ),
}
