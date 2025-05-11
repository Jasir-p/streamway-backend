from rest_framework import serializers
from tenant.models import TenantBilling, Invoice

class TenantBillingSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    active_count_users = serializers.SerializerMethodField()
    bill_amount = serializers.SerializerMethodField()
    class Meta:
        model = TenantBilling
        fields = [
            'id', 'tenant_name', 'stripe_customer_id', 'billing_email', 
            'billing_name', 'per_user_rate', 'billing_expiry', 'is_active',
            'last_billed_date', 'next_billing_date','active_count_users','bill_amount'
        ]
        read_only_fields = ['id', 'tenant_name', 'stripe_customer_id', 'last_billed_date', 'next_billing_date','active_count_users','bill_amount']
    def active_count_users(self, obj):
        return obj.active_count_users
    def get_bill_amount(self,obj):
        bill_amount,_= obj.calculate_bill_amount()
        return bill_amount

class InvoiceSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant_billing.tenant.name', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'tenant_name', 'stripe_invoice_id', 'stripe_payment_intent_id',
            'amount', 'user_count', 'status', 'created_at', 'paid_at', 'invoice_pdf_url'
        ]
        read_only_fields = [
            'id', 'tenant_name', 'stripe_invoice_id', 'stripe_payment_intent_id',
            'amount', 'user_count', 'status', 'created_at', 'paid_at', 'invoice_pdf_url'
        ]