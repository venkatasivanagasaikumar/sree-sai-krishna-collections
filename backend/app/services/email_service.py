import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.database import db_manager

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
        template_name: str = "generic"
    ) -> Dict[str, Any]:
        """Dispatches an email via SMTP or logs to database if credentials are not configured."""
        sent_status = "simulated"
        error_msg = None

        if cls._is_configured():
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
                msg["To"] = to_email

                if text_body:
                    msg.attach(MIMEText(text_body, "plain"))
                msg.attach(MIMEText(html_body, "html"))

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

        # Persist email dispatch record in database
        log_entry = {
            "to_email": to_email,
            "subject": subject,
            "template_name": template_name,
            "status": sent_status,
            "error": error_msg,
            "created_at": datetime.now(timezone.utc),
            "preview": text_body[:160] if text_body else html_body[:160]
        }
        try:
            if db_manager.db is not None:
                db_manager.db.email_logs.insert_one(log_entry)
                db_manager.persist_to_disk()
        except Exception as log_err:
            logger.warning(f"Failed to save email log: {log_err}")

        return {
            "status": sent_status,
            "to": to_email,
            "subject": subject,
            "template": template_name,
            "error": error_msg
        }

    @classmethod
    def send_password_reset(cls, to_email: str, token: str, customer_name: str = "Customer") -> Dict[str, Any]:
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        subject = "Reset Your Password - Sree Sai Krishna Collections"
        html = f"""
        <div style="font-family: 'Inter', -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #1e293b; border: 1px solid #e2e8f0; border-radius: 8px;">
            <div style="background-color: #123F7A; padding: 20px; border-radius: 6px; text-align: center;">
                <h1 style="color: #C89A43; margin: 0; font-size: 20px; font-weight: 600;">SREE SAI KRISHNA COLLECTIONS</h1>
                <p style="color: #ffffff; margin: 4px 0 0 0; font-size: 13px;">Fine Jewellery & Traditional Accessories</p>
            </div>
            <div style="padding: 24px 0;">
                <h2 style="font-size: 18px; color: #123F7A; font-weight: 600;">Password Reset Request</h2>
                <p>Hello {customer_name},</p>
                <p>We received a request to reset your password. Click the button below to choose a new password. This link is valid for 15 minutes and can only be used once.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background-color: #123F7A; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Reset Password</a>
                </div>
                <p style="font-size: 12px; color: #64748b;">If the button doesn't work, copy and paste this link in your browser:<br/><a href="{reset_link}">{reset_link}</a></p>
                <p style="font-size: 13px; color: #64748b; margin-top: 24px;">If you didn't request a password reset, you can safely ignore this email.</p>
            </div>
            <div style="border-top: 1px solid #e2e8f0; padding-top: 16px; font-size: 12px; color: #94a3b8; text-align: center;">
                &copy; {datetime.now().year} Sree Sai Krishna Collections. All rights reserved.
            </div>
        </div>
        """
        text = f"Hello {customer_name},\n\nReset your password using the link below (valid for 15 minutes):\n{reset_link}\n\nIf you did not make this request, please ignore this email."
        return cls.send_email(to_email, subject, html, text, "password_reset")

    @classmethod
    def send_email_verification(cls, to_email: str, token: str, customer_name: str = "Customer") -> Dict[str, Any]:
        verify_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        subject = "Verify Your Email - Sree Sai Krishna Collections"
        html = f"""
        <div style="font-family: 'Inter', -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #1e293b; border: 1px solid #e2e8f0; border-radius: 8px;">
            <div style="background-color: #123F7A; padding: 20px; border-radius: 6px; text-align: center;">
                <h1 style="color: #C89A43; margin: 0; font-size: 20px; font-weight: 600;">SREE SAI KRISHNA COLLECTIONS</h1>
            </div>
            <div style="padding: 24px 0;">
                <h2 style="font-size: 18px; color: #123F7A; font-weight: 600;">Welcome to SSK Collections!</h2>
                <p>Hello {customer_name},</p>
                <p>Thank you for joining our community of jewellery enthusiasts. Please verify your email address to complete your profile setup.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_link}" style="background-color: #C89A43; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Verify Email</a>
                </div>
                <p style="font-size: 12px; color: #64748b;">Link: <a href="{verify_link}">{verify_link}</a></p>
            </div>
        </div>
        """
        text = f"Welcome {customer_name}!\n\nPlease verify your email address:\n{verify_link}"
        return cls.send_email(to_email, subject, html, text, "email_verification")

    @classmethod
    def send_order_confirmation(cls, to_email: str, order: Dict[str, Any]) -> Dict[str, Any]:
        order_id = order.get("order_id", "SSK-ORDER")
        total = order.get("final_total", order.get("total_amount", 0.0))
        subject = f"Order Confirmed #{order_id} - Sree Sai Krishna Collections"
        items_html = ""
        for itm in order.get("items", []):
            items_html += f"<tr><td style='padding: 8px 0; border-bottom: 1px solid #f1f5f9;'>{itm.get('name', 'Jewellery item')} x{itm.get('quantity', 1)}</td><td style='padding: 8px 0; border-bottom: 1px solid #f1f5f9; text-align: right;'>₹{itm.get('price', 0.0):.2f}</td></tr>"

        html = f"""
        <div style="font-family: 'Inter', -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #1e293b; border: 1px solid #e2e8f0; border-radius: 8px;">
            <div style="background-color: #123F7A; padding: 20px; border-radius: 6px; text-align: center;">
                <h1 style="color: #C89A43; margin: 0; font-size: 20px; font-weight: 600;">SREE SAI KRISHNA COLLECTIONS</h1>
                <p style="color: #ffffff; margin: 4px 0 0 0; font-size: 13px;">Order Confirmation</p>
            </div>
            <div style="padding: 24px 0;">
                <h2 style="font-size: 18px; color: #123F7A;">Thank you for your order!</h2>
                <p>Your order <strong>#{order_id}</strong> has been received and is being prepared with utmost care.</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
                    <thead>
                        <tr style="border-bottom: 2px solid #e2e8f0; text-align: left;">
                            <th style="padding: 8px 0;">Item</th>
                            <th style="padding: 8px 0; text-align: right;">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td style="padding: 12px 0; font-weight: 600;">Total Paid:</td>
                            <td style="padding: 12px 0; font-weight: 600; text-align: right; color: #123F7A;">₹{total:.2f}</td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>
        """
        text = f"Thank you for your order #{order_id}!\nTotal Amount: ₹{total:.2f}\nWe will notify you once your order is dispatched."
        return cls.send_email(to_email, subject, html, text, "order_confirmation")

    @classmethod
    def send_shipment_notification(cls, to_email: str, order: Dict[str, Any], tracking_data: Dict[str, Any]) -> Dict[str, Any]:
        order_id = order.get("order_id", "SSK-ORDER")
        carrier = tracking_data.get("carrier", "Blue Dart / Delhivery")
        awb = tracking_data.get("awb", "N/A")
        tracking_url = tracking_data.get("tracking_url", "#")
        subject = f"Your SSK Order #{order_id} Has Shipped!"
        html = f"""
        <div style="font-family: 'Inter', -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #1e293b; border: 1px solid #e2e8f0; border-radius: 8px;">
            <div style="background-color: #123F7A; padding: 20px; border-radius: 6px; text-align: center;">
                <h1 style="color: #C89A43; margin: 0; font-size: 20px; font-weight: 600;">SREE SAI KRISHNA COLLECTIONS</h1>
            </div>
            <div style="padding: 24px 0;">
                <h2 style="font-size: 18px; color: #123F7A;">Your Order Is On Its Way!</h2>
                <p>Good news! Your order <strong>#{order_id}</strong> has been shipped via <strong>{carrier}</strong>.</p>
                <div style="background: #f8fafc; padding: 16px; border-radius: 6px; margin: 20px 0; border: 1px solid #e2e8f0;">
                    <p style="margin: 0 0 8px 0;"><strong>Carrier:</strong> {carrier}</p>
                    <p style="margin: 0 0 12px 0;"><strong>AWB / Tracking Number:</strong> {awb}</p>
                    <a href="{tracking_url}" style="background-color: #123F7A; color: #ffffff; padding: 8px 20px; text-decoration: none; border-radius: 4px; font-size: 13px; font-weight: 600; display: inline-block;">Track Shipment</a>
                </div>
            </div>
        </div>
        """
        text = f"Your order #{order_id} has shipped via {carrier} (AWB: {awb}). Track here: {tracking_url}"
        return cls.send_email(to_email, subject, html, text, "shipment_notification")

    @classmethod
    def send_refund_notification(cls, to_email: str, order_id: str, amount: float, reason: str = "") -> Dict[str, Any]:
        subject = f"Refund Processed for Order #{order_id} - Sree Sai Krishna Collections"
        html = f"""
        <div style="font-family: 'Inter', -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #1e293b; border: 1px solid #e2e8f0; border-radius: 8px;">
            <div style="background-color: #123F7A; padding: 20px; border-radius: 6px; text-align: center;">
                <h1 style="color: #C89A43; margin: 0; font-size: 20px; font-weight: 600;">SREE SAI KRISHNA COLLECTIONS</h1>
            </div>
            <div style="padding: 24px 0;">
                <h2 style="font-size: 18px; color: #123F7A;">Refund Confirmation</h2>
                <p>A refund of <strong>₹{amount:.2f}</strong> has been initiated for order <strong>#{order_id}</strong>.</p>
                {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
                <p style="font-size: 13px; color: #64748b;">It typically takes 5–7 business days for the amount to reflect in your original payment method or bank account.</p>
            </div>
        </div>
        """
        text = f"Refund of ₹{amount:.2f} initiated for order #{order_id}. Funds will reflect in 5-7 business days."
        return cls.send_email(to_email, subject, html, text, "refund_notification")
