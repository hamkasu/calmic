"""
PhotoVault Billing Blueprint
Handles subscription management, Stripe checkout, and billing for Malaysian market
"""
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from photovault.extensions import db
from photovault.models import SubscriptionPlan, UserSubscription, Invoice, PaymentHistory
import stripe
import os

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

# Initialize Stripe with API key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


@billing_bp.route('/plans')
def plans():
    """Display available subscription plans"""
    from sqlalchemy.exc import OperationalError, DatabaseError
    import time
    
    # Retry logic for database connection issues
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.sort_order).all()
            
            # Check if any plans exist - if not, seed them
            if not plans:
                current_app.logger.warning("No subscription plans found in database, attempting to seed...")
                try:
                    from photovault import _seed_subscription_plans
                    _seed_subscription_plans(current_app._get_current_object())
                    # Try to fetch plans again after seeding
                    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.sort_order).all()
                except Exception as seed_error:
                    current_app.logger.error(f"Failed to seed subscription plans: {str(seed_error)}")
            
            # Get user's current subscription if logged in
            current_subscription = None
            if current_user.is_authenticated:
                current_subscription = UserSubscription.query.filter_by(
                    user_id=current_user.id,
                    status='active'
                ).first()
            
            return render_template('billing/plans.html', 
                                 plans=plans, 
                                 current_subscription=current_subscription)
        except (OperationalError, DatabaseError) as e:
            retry_count += 1
            current_app.logger.warning(f"Database error (attempt {retry_count}/{max_retries}): {str(e)}")
            
            # Close and remove the session to force a new connection
            db.session.remove()
            
            # Wait a bit before retrying (exponential backoff)
            if retry_count < max_retries:
                time.sleep(0.5 * retry_count)
            else:
                current_app.logger.error(f"Failed to connect to database after {max_retries} attempts: {str(e)}")
                # Provide helpful error message for Railway deployment
                error_msg = 'Unable to load pricing information. '
                if 'could not connect' in str(e).lower() or 'connection' in str(e).lower():
                    error_msg += 'Database connection failed. Please ensure DATABASE_URL is configured on Railway.'
                else:
                    error_msg += 'Please try again later.'
                flash(error_msg, 'danger')
                return render_template('errors/500.html'), 500
        except Exception as e:
            current_app.logger.error(f"Unexpected error loading plans: {str(e)}")
            flash('An unexpected error occurred. Please contact support.', 'danger')
            return render_template('errors/500.html'), 500


@billing_bp.route('/subscribe/<int:plan_id>', methods=['POST'])
@login_required
def subscribe(plan_id):
    """Create Stripe checkout session for subscription or direct subscribe in development"""
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # Check if user already has an active subscription
    existing_sub = UserSubscription.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).first()
    
    if existing_sub:
        flash('You already have an active subscription. Please cancel it first before subscribing to a new plan.', 'warning')
        return redirect(url_for('billing.dashboard'))
    
    # Check if Stripe is configured
    stripe_configured = bool(os.getenv('STRIPE_SECRET_KEY'))
    
    # Development mode: create subscription directly without Stripe
    if not stripe_configured:
        try:
            # Create user subscription record directly
            user_sub = UserSubscription(
                user_id=current_user.id,
                plan_id=plan_id,
                status='active',
                start_date=datetime.utcnow(),
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                next_billing_date=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(user_sub)
            db.session.commit()
            
            current_app.logger.info(f"Development mode: User {current_user.id} subscribed to {plan.name}")
            flash(f'Successfully subscribed to {plan.display_name}! (Development mode - no payment required)', 'success')
            return redirect(url_for('billing.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating subscription in development mode: {str(e)}")
            flash(f'Error creating subscription: {str(e)}', 'danger')
            return redirect(url_for('billing.plans'))
    
    # Production mode: use Stripe
    try:
        # Create or get Stripe customer
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.username,
                metadata={'user_id': current_user.id}
            )
            customer_id = customer.id
            # Save customer ID to user
            current_user.stripe_customer_id = customer_id
            db.session.commit()
        else:
            customer_id = current_user.stripe_customer_id
        
        # Calculate price in cents (Stripe uses smallest currency unit)
        # For MYR: 1 MYR = 100 sen
        total_price = plan.total_price_myr
        price_in_sen = int(total_price * 100)
        
        # Create Stripe checkout session
        success_url = url_for('billing.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = url_for('billing.plans', _external=True)
        
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],  # Only card for subscriptions (FPX doesn't support recurring)
            line_items=[{
                'price_data': {
                    'currency': 'myr',
                    'product_data': {
                        'name': plan.display_name,
                        'description': plan.description,
                    },
                    'unit_amount': price_in_sen,
                    'recurring': {'interval': 'month'}
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': current_user.id,
                'plan_id': plan.id,
                'plan_name': plan.name
            }
        )
        
        return redirect(checkout_session.url, code=303)
        
    except Exception as e:
        current_app.logger.error(f"Stripe checkout error: {str(e)}")
        flash(f'Error creating checkout session: {str(e)}', 'danger')
        return redirect(url_for('billing.plans'))


@billing_bp.route('/success')
@login_required
def success():
    """Handle successful subscription payment"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Invalid session', 'danger')
        return redirect(url_for('billing.dashboard'))
    
    try:
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Get subscription details
            subscription = stripe.Subscription.retrieve(session.subscription)
            
            # Get plan from metadata
            plan_id = int(session.metadata.get('plan_id'))
            plan = SubscriptionPlan.query.get(plan_id)
            
            # Create user subscription record
            user_sub = UserSubscription(
                user_id=current_user.id,
                plan_id=plan_id,
                status='active',
                stripe_subscription_id=subscription.id,
                stripe_customer_id=session.customer,
                start_date=datetime.utcnow(),
                current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end),
                next_billing_date=datetime.fromtimestamp(subscription.current_period_end)
            )
            db.session.add(user_sub)
            db.session.flush()  # Flush to assign ID to user_sub
            
            # Create invoice
            invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m')}-{current_user.id:04d}"
            invoice = Invoice(
                invoice_number=invoice_number,
                user_id=current_user.id,
                subscription_id=user_sub.id,
                billing_name=current_user.username,
                billing_email=current_user.email,
                subtotal=plan.price_myr,
                sst_rate=plan.sst_rate,
                sst_amount=Decimal(str(plan.sst_amount)),
                total=Decimal(str(plan.total_price_myr)),
                currency='MYR',
                description=f"{plan.display_name} Subscription",
                status='paid',
                issue_date=datetime.utcnow(),
                paid_date=datetime.utcnow(),
                stripe_invoice_id=session.invoice if hasattr(session, 'invoice') else None,
                stripe_payment_intent_id=session.payment_intent
            )
            db.session.add(invoice)
            
            # Create payment history record
            payment = PaymentHistory(
                user_id=current_user.id,
                invoice_id=invoice.id,
                amount=Decimal(str(plan.total_price_myr)),
                currency='MYR',
                stripe_payment_intent_id=session.payment_intent,
                payment_method='card',
                status='succeeded',
                description=f"Subscription to {plan.display_name}",
                payment_date=datetime.utcnow()
            )
            db.session.add(payment)
            
            db.session.commit()
            
            flash(f'Successfully subscribed to {plan.display_name}!', 'success')
        else:
            flash('Payment not completed. Please try again.', 'warning')
            
    except Exception as e:
        current_app.logger.error(f"Error processing subscription success: {str(e)}")
        flash('Error processing subscription. Please contact support.', 'danger')
    
    return redirect(url_for('billing.dashboard'))


@billing_bp.route('/dashboard')
@login_required
def dashboard():
    """User billing dashboard"""
    # Get active subscription
    subscription = UserSubscription.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).first()
    
    # Get invoices
    invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.created_at.desc()).limit(10).all()
    
    # Get payment history
    payments = PaymentHistory.query.filter_by(user_id=current_user.id).order_by(PaymentHistory.created_at.desc()).limit(10).all()
    
    return render_template('billing/dashboard.html',
                         subscription=subscription,
                         invoices=invoices,
                         payments=payments)


@billing_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel user subscription"""
    subscription = UserSubscription.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).first()
    
    if not subscription:
        flash('No active subscription found.', 'warning')
        return redirect(url_for('billing.dashboard'))
    
    try:
        # Cancel Stripe subscription at period end
        stripe_sub = stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        # Update local subscription
        subscription.cancel_at_period_end = True
        subscription.cancel_reason = request.form.get('reason', 'User requested cancellation')
        db.session.commit()
        
        flash('Your subscription will be canceled at the end of the current billing period.', 'info')
        
    except Exception as e:
        current_app.logger.error(f"Error canceling subscription: {str(e)}")
        flash(f'Error canceling subscription: {str(e)}', 'danger')
    
    return redirect(url_for('billing.dashboard'))


@billing_bp.route('/reactivate', methods=['POST'])
@login_required
def reactivate_subscription():
    """Reactivate a canceled subscription"""
    subscription = UserSubscription.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).first()
    
    if not subscription or not subscription.cancel_at_period_end:
        flash('No canceled subscription found.', 'warning')
        return redirect(url_for('billing.dashboard'))
    
    try:
        # Reactivate Stripe subscription
        stripe_sub = stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=False
        )
        
        # Update local subscription
        subscription.cancel_at_period_end = False
        subscription.cancel_reason = None
        db.session.commit()
        
        flash('Your subscription has been reactivated!', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Error reactivating subscription: {str(e)}")
        flash(f'Error reactivating subscription: {str(e)}', 'danger')
    
    return redirect(url_for('billing.dashboard'))


@billing_bp.route('/upgrade/<int:plan_id>', methods=['POST'])
@login_required
def upgrade_plan(plan_id):
    """Upgrade or change subscription plan"""
    new_plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # Get current subscription
    subscription = UserSubscription.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).first()
    
    if not subscription:
        flash('No active subscription found. Please subscribe first.', 'warning')
        return redirect(url_for('billing.plans'))
    
    # Verify ownership
    if subscription.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('billing.dashboard'))
    
    if subscription.plan_id == plan_id:
        flash('You are already on this plan.', 'info')
        return redirect(url_for('billing.dashboard'))
    
    # Check if Stripe is configured
    stripe_configured = bool(os.getenv('STRIPE_SECRET_KEY'))
    
    # Development mode: allow plan changes without Stripe
    if not stripe_configured:
        try:
            current_plan = subscription.plan
            subscription.plan_id = plan_id
            db.session.commit()
            
            current_app.logger.info(f"Development mode: User {current_user.id} changed plan from {current_plan.name} to {new_plan.name}")
            flash(f'Successfully changed to {new_plan.display_name}! (Development mode - no payment required)', 'success')
            return redirect(url_for('billing.dashboard'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error changing plan in development mode: {str(e)}")
            flash(f'Error changing plan: {str(e)}', 'danger')
            return redirect(url_for('billing.dashboard'))
    
    # Production mode: require Stripe integration
    # Check if new plan has Stripe price ID configured
    if not new_plan.stripe_price_id:
        flash('This plan is not available for online subscription. Please contact support.', 'warning')
        return redirect(url_for('billing.plans'))
    
    try:
        current_plan = subscription.plan
        is_upgrade = new_plan.price_myr > current_plan.price_myr
        
        # Retrieve the Stripe subscription and verify customer ownership
        stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
        
        # Verify customer ownership for security
        if stripe_sub.customer != subscription.stripe_customer_id:
            current_app.logger.error(f"Customer mismatch for subscription {subscription.id}")
            flash('Unauthorized access to subscription.', 'danger')
            return redirect(url_for('billing.dashboard'))
        
        # For upgrades: apply immediately with proration (payment required before entitlement)
        # For downgrades/changes: requires Stripe Price IDs - show message to contact support
        if is_upgrade:
            # Immediate upgrade with proration - require successful payment
            updated_sub = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': stripe_sub['items']['data'][0].id,
                    'price': new_plan.stripe_price_id,
                }],
                proration_behavior='create_prorations',
                payment_behavior='error_if_incomplete'  # Require successful payment
            )
            
            # Only update entitlements after successful payment
            if updated_sub.status == 'active':
                subscription.plan_id = plan_id
                subscription.current_period_start = datetime.fromtimestamp(updated_sub.current_period_start)
                subscription.current_period_end = datetime.fromtimestamp(updated_sub.current_period_end)
                db.session.commit()
                
                flash(f'Successfully upgraded to {new_plan.display_name}! You have been charged a prorated amount.', 'success')
            else:
                # Payment requires action - inform user
                flash(f'Your upgrade requires payment confirmation. Please check your payment method.', 'warning')
        else:
            # For downgrades: simplified approach - inform user to contact support
            # Full implementation requires proper Stripe Price ID configuration and Subscription Schedules
            flash(f'To switch to {new_plan.display_name}, please contact support for assistance. Downgrades will be processed at the end of your current billing period.', 'info')
        
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe error upgrading plan: {str(e)}")
        flash(f'Payment error: {str(e)}', 'danger')
    except Exception as e:
        current_app.logger.error(f"Error upgrading plan: {str(e)}")
        flash(f'Error upgrading plan: {str(e)}', 'danger')
    
    return redirect(url_for('billing.dashboard'))


@billing_bp.route('/invoice/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    """View invoice details"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Ensure user owns this invoice
    if invoice.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('billing.dashboard'))
    
    return render_template('billing/invoice.html', invoice=invoice)


@billing_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for subscription events"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle the event
    if event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_payment_succeeded(invoice)
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failed(invoice)
    
    return jsonify({'status': 'success'}), 200


def handle_subscription_updated(stripe_subscription):
    """Handle subscription update webhook"""
    subscription = UserSubscription.query.filter_by(
        stripe_subscription_id=stripe_subscription['id']
    ).first()
    
    if subscription:
        # Update subscription dates and status
        subscription.current_period_start = datetime.fromtimestamp(stripe_subscription['current_period_start'])
        subscription.current_period_end = datetime.fromtimestamp(stripe_subscription['current_period_end'])
        subscription.status = stripe_subscription['status']
        
        # Update plan_id based on the actual Stripe subscription item price
        if stripe_subscription.get('items') and stripe_subscription['items'].get('data'):
            stripe_price_id = stripe_subscription['items']['data'][0].get('price', {}).get('id')
            if stripe_price_id:
                # Find the plan with matching Stripe price ID
                new_plan = SubscriptionPlan.query.filter_by(stripe_price_id=stripe_price_id).first()
                if new_plan and new_plan.id != subscription.plan_id:
                    # Plan has changed (e.g., scheduled downgrade took effect)
                    subscription.plan_id = new_plan.id
                    current_app.logger.info(f"Updated subscription {subscription.id} to plan {new_plan.name}")
        
        db.session.commit()


def handle_subscription_deleted(stripe_subscription):
    """Handle subscription deletion webhook"""
    subscription = UserSubscription.query.filter_by(
        stripe_subscription_id=stripe_subscription['id']
    ).first()
    
    if subscription:
        subscription.status = 'canceled'
        subscription.ended_at = datetime.utcnow()
        db.session.commit()


def handle_payment_succeeded(stripe_invoice):
    """Handle successful payment webhook"""
    # Update invoice status
    invoice = Invoice.query.filter_by(
        stripe_invoice_id=stripe_invoice['id']
    ).first()
    
    if invoice:
        invoice.status = 'paid'
        invoice.paid_date = datetime.utcnow()
        db.session.commit()


def handle_payment_failed(stripe_invoice):
    """Handle failed payment webhook"""
    # Log payment failure
    current_app.logger.error(f"Payment failed for invoice: {stripe_invoice['id']}")
    # You could send email notification here


# ============================================================================
# ADMIN BILLING ROUTES
# ============================================================================

@billing_bp.route('/admin')
@login_required
def admin_dashboard():
    """Admin billing dashboard with revenue and subscription metrics"""
    # Check if user is admin
    if not current_user.is_admin and not current_user.is_superuser:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    from sqlalchemy import func, extract
    
    # Get subscription statistics
    total_subscriptions = UserSubscription.query.filter_by(status='active').count()
    total_users = db.session.query(func.count(UserSubscription.user_id.distinct())).filter_by(status='active').scalar()
    
    # Get revenue statistics
    total_revenue = db.session.query(func.sum(Invoice.total)).filter_by(status='paid').scalar() or 0
    this_month_revenue = db.session.query(func.sum(Invoice.total)).filter(
        Invoice.status == 'paid',
        extract('year', Invoice.paid_date) == datetime.utcnow().year,
        extract('month', Invoice.paid_date) == datetime.utcnow().month
    ).scalar() or 0
    
    # Get plan distribution
    plan_stats = db.session.query(
        SubscriptionPlan.display_name,
        func.count(UserSubscription.id).label('count')
    ).join(UserSubscription).filter(
        UserSubscription.status == 'active'
    ).group_by(SubscriptionPlan.display_name).all()
    
    # Get recent subscriptions
    recent_subscriptions = UserSubscription.query.filter_by(
        status='active'
    ).order_by(UserSubscription.created_at.desc()).limit(10).all()
    
    # Get recent invoices
    recent_invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(20).all()
    
    # Get payment statistics
    successful_payments = PaymentHistory.query.filter_by(status='succeeded').count()
    failed_payments = PaymentHistory.query.filter_by(status='failed').count()
    
    return render_template('billing/admin_dashboard.html',
                         total_subscriptions=total_subscriptions,
                         total_users=total_users,
                         total_revenue=total_revenue,
                         this_month_revenue=this_month_revenue,
                         plan_stats=plan_stats,
                         recent_subscriptions=recent_subscriptions,
                         recent_invoices=recent_invoices,
                         successful_payments=successful_payments,
                         failed_payments=failed_payments)


@billing_bp.route('/admin/subscriptions')
@login_required
def admin_subscriptions():
    """View all subscriptions"""
    if not current_user.is_admin and not current_user.is_superuser:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    plan_filter = request.args.get('plan', 'all')
    
    # Build query
    query = UserSubscription.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if plan_filter != 'all':
        query = query.filter_by(plan_id=int(plan_filter))
    
    subscriptions = query.order_by(UserSubscription.created_at.desc()).all()
    plans = SubscriptionPlan.query.all()
    
    return render_template('billing/admin_subscriptions.html',
                         subscriptions=subscriptions,
                         plans=plans,
                         status_filter=status_filter,
                         plan_filter=plan_filter)


@billing_bp.route('/admin/invoices')
@login_required
def admin_invoices():
    """View all invoices"""
    if not current_user.is_admin and not current_user.is_superuser:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    
    # Build query
    query = Invoice.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    return render_template('billing/admin_invoices.html',
                         invoices=invoices,
                         status_filter=status_filter)


@billing_bp.route('/admin/revenue')
@login_required
def admin_revenue():
    """View revenue analytics"""
    if not current_user.is_admin and not current_user.is_superuser:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    from sqlalchemy import func, extract
    
    # Get monthly revenue for the last 12 months
    monthly_revenue = []
    for i in range(11, -1, -1):
        target_date = datetime.utcnow() - timedelta(days=30*i)
        revenue = db.session.query(func.sum(Invoice.total)).filter(
            Invoice.status == 'paid',
            extract('year', Invoice.paid_date) == target_date.year,
            extract('month', Invoice.paid_date) == target_date.month
        ).scalar() or 0
        
        monthly_revenue.append({
            'month': target_date.strftime('%b %Y'),
            'revenue': float(revenue)
        })
    
    # Get revenue by plan
    revenue_by_plan = db.session.query(
        SubscriptionPlan.display_name,
        func.sum(Invoice.total).label('revenue')
    ).join(UserSubscription).join(Invoice).filter(
        Invoice.status == 'paid'
    ).group_by(SubscriptionPlan.display_name).all()
    
    return render_template('billing/admin_revenue.html',
                         monthly_revenue=monthly_revenue,
                         revenue_by_plan=revenue_by_plan)
