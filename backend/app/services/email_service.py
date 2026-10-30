import smtplib
import os
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.logging import logger
from app.database import db_manager

def _get_base_template(title: str, content_html: str, action_button_text: str = "", action_button_url: str = "") -> str:
    btn_html = ""
    if action_button_text and action_button_url:
        btn_html = f"""
        <div style="text-align: center; margin: 28px 0;">
            <a href="{action_button_url}" style="background-color: #123F7A; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 13px; display: inline-block;">
                {action_button_text} &rarr;
            </a>
        </div>
        """
    return f"""
    <div style="font-family: 'Inter', -apple-system, sans-serif; max-width: 620px; margin: 0 auto; padding: 24px; color: #1e293b; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;">
        <div style="background-color: #123F7A; padding: 20px; border-radius: 6px; text-align: center;">
            <h1 style="color: #C89A43; margin: 0; font-size: 20px; font-weight: 600; letter-spacing: 1px;">SREE SAI KRISHNA COLLECTIONS</h1>
            <p style="color: #ffffff; margin: 4px 0 0 0; font-size: 12px;">Precious Traditional Jewellery & Women's Fashion Accessories</p>
        </div>
        <div style="padding: 24px 8px;">
            <h2 style="font-size: 18px; color: #123F7A; font-weight: 600; margin-top: 0;">{title}</h2>
            {content_html}
            {btn_html}
        </div>
        <div style="border-top: 1px solid #e2e8f0; padding-top: 16px; font-size: 11px; color: #94a3b8; text-align: center; line-height: 1.5;">
            Shop #12, Sri Krishna Temple Street, Near Clock Tower, Secunderabad, Telangana - 500003<br/>
            Helpline: {settings.SUPPORT_PHONE} | Email: {settings.SUPPORT_EMAIL}<br/>
            &copy; {datetime.now().year} Sree Sai Krishna Collections. All rights reserved.
        </div>
    </div>
    """

class EmailService:
    @staticmethod
    def _is_configured() -> bool:
        return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        template_name: str = "generic",
        order_id: Optional[str] = None,
        attachment_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dispatches an email via SMTP or logs to database if credentials are not configured."""
        sent_status = "simulated"
        error_msg = None
        notification_id = f"eml_{uuid.uuid4().hex[:14]}"
        now = datetime.now(timezone.utc)

        if cls._is_configured():
            try:
                msg = MIMEMultipart("mixed")
                msg["Subject"] = subject
                msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
                msg["To"] = to_email

                body_part = MIMEMultipart("alternative")
                if text_body:
                    body_part.attach(MIMEText(text_body, "plain"))
                body_part.attach(MIMEText(html_body, "html"))
                msg.attach(body_part)

                # Attach PDF file if available
                if attachment_path and os.path.exists(attachment_path):
                    with open(attachment_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                    part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                    msg.attach(part)

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    if settings.SMTP_TLS:
                        server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
                sent_status = "delivered"
                logger.info(f"Email [{template_name}] successfully sent to {to_email}")
            except Exception as e:
                sent_status = "failed"
                error_msg = str(e)
                logger.error(f"Failed to send email to {to_email}: {e}")
        else:
            logger.info(f"SMTP not configured. Email [{template_name}] to {to_email} saved to email_logs (simulated).")

        # Persist record in both email_logs and centralized notification_logs
        log_entry = {
            "notification_id": notification_id,
            "channel": "email",
            "to_email": to_email,
            "recipient": to_email,
            "order_id": order_id,
            "subject": subject,
            "template_name": template_name,
            "status": sent_status,
            "error": error_msg,
            "created_at": now,
            "preview": text_body[:160] if text_body else html_body[:160]
        }
        try:
            db = db_manager.db
            if db is not None:
                db.email_logs.insert_one(dict(log_entry))
                db.notification_logs.insert_one(dict(log_entry))
                db_manager.persist_to_disk()
        except Exception as log_err:
            logger.warning(f"Failed to save email log: {log_err}")

        return {
            "success": sent_status in ["delivered", "simulated"],
            "status": sent_status,
            "to": to_email,
            "subject": subject,
            "template": template_name,
            "notification_id": notification_id,
            "error": error_msg
        }

    @classmethod
    def send_password_reset(cls, to_email: str, token: str, customer_name: str = "Customer") -> Dict[str, Any]:
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        subject = "Reset Your Password - Sree Sai Krishna Collections"
        content = f"""
        <p>Hello {customer_name},</p>
        <p>We received a request to reset your SSK account password. Click the button below to choose a new password. This link is valid for 15 minutes and can only be used once.</p>
        <p style="font-size: 11px; color: #64748b;">If you didn't request a password reset, you can safely ignore this email.</p>
        """
        html = _get_base_template("Password Reset Request", content, "Reset My Password", reset_link)
        text = f"Hello {customer_name},\n\nReset your password (valid 15 min):\n{reset_link}"
        return cls.send_email(to_email, subject, html, text, "password_reset")

    @classmethod
    def send_email_verification(cls, to_email: str, token: str, customer_name: str = "Customer") -> Dict[str, Any]:
        verify_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        subject = "Verify Your Email - Sree Sai Krishna Collections"
        content = f"""
        <p>Hello {customer_name},</p>
        <p>Thank you for joining Sree Sai Krishna Collections. Please click below to verify your email address and activate all member benefits.</p>
        """
        html = _get_base_template("Welcome to SSK Collections!", content, "Verify Email Address", verify_link)
        text = f"Welcome {customer_name}!\nVerify your email:\n{verify_link}"
        return cls.send_email(to_email, subject, html, text, "email_verification")

    @classmethod
    def send_order_confirmation(cls, to_email: str, order: Dict[str, Any], invoice_number: Optional[str] = None) -> Dict[str, Any]:
        order_id = order.get("order_id", "SSK-ORDER")
        total = float(order.get("final_total", order.get("final_amount", 0.0)))
        items_html = ""
        for itm in order.get("items", []):
            items_html += f"<tr><td style='padding: 6px 0; border-bottom: 1px solid #f1f5f9;'>{itm.get('name', 'Jewellery item')} x{itm.get('quantity', 1)}</td><td style='padding: 6px 0; border-bottom: 1px solid #f1f5f9; text-align: right;'>₹{itm.get('price', 0.0):.2f}</td></tr>"

        tracking_link = f"{settings.FRONTEND_URL}/account/orders/{order_id}"
        inv_note = f"<p style='font-size: 12px; color: #123F7A;'><b>Tax Invoice #:</b> {invoice_number}</p>" if invoice_number else ""
        content = f"""
        <p>Your order <strong>#{order_id}</strong> has been confirmed!</p>
        {inv_note}
        <table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px;">
            <thead>
                <tr style="border-bottom: 2px solid #e2e8f0; text-align: left; color: #123F7A;">
                    <th style="padding: 6px 0;">Item</th>
                    <th style="padding: 6px 0; text-align: right;">Amount</th>
                </tr>
            </thead>
            <tbody>{items_html}</tbody>
            <tfoot>
                <tr>
                    <td style="padding: 10px 0; font-weight: 600;">Total Amount:</td>
                    <td style="padding: 10px 0; font-weight: 600; text-align: right; color: #123F7A;">₹{total:.2f}</td>
                </tr>
            </tfoot>
        </table>
        """
        html = _get_base_template(f"Order Confirmed #{order_id}", content, "View Order & Download Invoice", tracking_link)
        text = f"Order #{order_id} Confirmed! Total: ₹{total:.2f}. Track order: {tracking_link}"
        return cls.send_email(to_email, f"Order Confirmed #{order_id} - Sree Sai Krishna Collections", html, text, "order_confirmation", order_id)

    @classmethod
    def send_order_packed(cls, to_email: str, order: Dict[str, Any]) -> Dict[str, Any]:
        order_id = order.get("order_id", "SSK-ORDER")
        tracking_link = f"{settings.FRONTEND_URL}/account/orders/{order_id}"
        content = f"""
        <p>Great news! Your items for order <strong>#{order_id}</strong> have been packed in our tamper-evident signature jewellery packaging and are ready for handover to our express courier partner.</p>
        """
        html = _get_base_template(f"Order #{order_id} Is Packed", content, "Track Status", tracking_link)
        text = f"Order #{order_id} is packed and ready for dispatch. Track: {tracking_link}"
        return cls.send_email(to_email, f"Your SSK order #{order_id} is packed!", html, text, "order_packed", order_id)

    @classmethod
    def send_shipment_notification(cls, to_email: str, order: Dict[str, Any], tracking_data: Dict[str, Any]) -> Dict[str, Any]:
        order_id = order.get("order_id", "SSK-ORDER")
        carrier = tracking_data.get("carrier", "Blue Dart Express")
        awb = tracking_data.get("awb", "N/A")
        tracking_url = tracking_data.get("tracking_url", f"{settings.FRONTEND_URL}/account/orders/{order_id}")
        content = f"""
        <p>Your order <strong>#{order_id}</strong> is on its way!</p>
        <div style="background: #f8fafc; padding: 14px; border-radius: 6px; margin: 16px 0; border: 1px solid #e2e8f0; font-size: 13px;">
            <p style="margin: 0 0 6px 0;"><strong>Courier:</strong> {carrier}</p>
            <p style="margin: 0 0 6px 0;"><strong>AWB / Tracking Number:</strong> {awb}</p>
        </div>
        """
        html = _get_base_template(f"Your Order Has Shipped! #{order_id}", content, "Track Package Live", tracking_url)
        text = f"Order #{order_id} shipped via {carrier} (AWB: {awb}). Track here: {tracking_url}"
        return cls.send_email(to_email, f"Your SSK order #{order_id} has been shipped!", html, text, "shipment_notification", order_id)

    @classmethod
    def send_out_for_delivery(cls, to_email: str, order: Dict[str, Any], tracking_data: Dict[str, Any]) -> Dict[str, Any]:
        order_id = order.get("order_id", "SSK-ORDER")
        awb = tracking_data.get("awb", "")
        content = f"""
        <p>Your order <strong>#{order_id}</strong> is out for delivery today! The delivery executive will reach your address shortly.</p>
        <p style="font-size: 12px; color: #64748b;">Please ensure someone is available at your delivery location.</p>
        """
        html = _get_base_template(f"Out for Delivery Today #{order_id}", content, "Track Delivery", f"{settings.FRONTEND_URL}/account/orders/{order_id}")
        text = f"Order #{order_id} is out for delivery today!"
        return cls.send_email(to_email, f"Your SSK order #{order_id} is out for delivery!", html, text, "out_for_delivery", order_id)

    @classmethod
    def send_order_delivered(cls, to_email: str, order: Dict[str, Any]) -> Dict[str, Any]:
        order_id = order.get("order_id", "SSK-ORDER")
        review_url = f"{settings.FRONTEND_URL}/account/orders/{order_id}"
        content = f"""
        <p>Your order <strong>#{order_id}</strong> has been successfully delivered. We hope your new jewellery pieces bring elegance and joy!</p>
        <p>If you have any feedback or require assistance, our customer care team is always here to help.</p>
        """
        html = _get_base_template(f"Order Delivered #{order_id}", content, "Rate Your Purchase & View Invoice", review_url)
        text = f"Order #{order_id} delivered! View invoice: {review_url}"
        return cls.send_email(to_email, f"Your SSK order #{order_id} has been delivered!", html, text, "order_delivered", order_id)

    @classmethod
    def send_cancellation_notification(cls, to_email: str, order: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
        order_id = order.get("order_id", "SSK-ORDER")
        content = f"""
        <p>Order <strong>#{order_id}</strong> has been cancelled.</p>
        {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
        <p>If you made a payment online, your refund will be processed back to your original payment method automatically.</p>
        """
        html = _get_base_template(f"Order #{order_id} Cancelled", content, "Shop Other Collections", f"{settings.FRONTEND_URL}/shop")
        text = f"Order #{order_id} cancelled. Reason: {reason}"
        return cls.send_email(to_email, f"Order #{order_id} Cancelled - Sree Sai Krishna Collections", html, text, "order_cancelled", order_id)

    @classmethod
    def send_refund_notification(cls, to_email: str, order_id: str, amount: float, reason: str = "") -> Dict[str, Any]:
        content = f"""
        <p>A refund of <strong>₹{amount:.2f}</strong> has been initiated for order <strong>#{order_id}</strong>.</p>
        {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
        <p style="font-size: 12px; color: #64748b;">It typically takes 5–7 business days for the credit to reflect on your bank or card statement.</p>
        """
        html = _get_base_template(f"Refund Processed #{order_id}", content, "Visit Account", f"{settings.FRONTEND_URL}/account")
        text = f"Refund of ₹{amount:.2f} initiated for order #{order_id}."
        return cls.send_email(to_email, f"Refund Processed for Order #{order_id} - Sree Sai Krishna Collections", html, text, "refund_notification", order_id)
