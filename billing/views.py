from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import stripe
from django.conf import settings
from tenant.models import TenantBilling, Invoice
from .serializers import TenantBillingSerializer, InvoiceSerializer
from .tasks import generate_invoice
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view,permission_classes

stripe.api_key = settings.STRIPE_SECRET_KEY

class TenantBillingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tenant billing management
    """
    serializer_class = TenantBillingSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):

        return TenantBilling.objects.filter(tenant=self.request.tenant)
    
    def list(self, request):

        try:
            billing = TenantBilling.objects.get(tenant=request.tenant)
            serializer = self.get_serializer(billing)
            return Response(serializer.data)
        except TenantBilling.DoesNotExist:
            return Response({'error': 'No billing configuration found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def generate_invoice(self, request):
        """
        Manually generate an invoice for the current tenant
        """
        try:
            billing = TenantBilling.objects.get(tenant=request.tenant)
            

            task = generate_invoice.delay(billing.id)
            
            return Response({
                'message': 'Invoice generation initiated',
                'task_id': task.id
            })
        except TenantBilling.DoesNotExist:
            return Response(
                {'error': 'No billing configuration found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing invoices
    """
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):

        try:
            billing = TenantBilling.objects.get(tenant=self.request.tenant)
            return Invoice.objects.filter(tenant_billing=billing).order_by('-created_at')
        except TenantBilling.DoesNotExist:
            return Invoice.objects.none()
    
    @action(detail=True, methods=['get'])
    def payment_intent(self, request, pk=None):
        """
        Get payment intent client secret for an invoice
        """
        invoice = self.get_object()
        
        if not invoice.stripe_payment_intent_id:
            return Response(
                {'error': 'No payment intent found for this invoice'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Retrieve the payment intent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(invoice.stripe_payment_intent_id)
            
            return Response({
                'client_secret': payment_intent.client_secret,
                'invoice': InvoiceSerializer(invoice).data
            })
        except stripe.error.StripeError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def mark_as_paid(self, request, pk=None):
        """
        Mark an invoice as paid (for testing purposes)
        """
        invoice = self.get_object()
        
        if invoice.status == 'paid':
            return Response({'message': 'Invoice already paid'})
        
        invoice.status = 'paid'
        invoice.save()
        
        return Response({'message': 'Invoice marked as paid'})
    


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_invoice_status(request):
    """
    Get the status of an invoice
    """
    tenant_billing_info = TenantBilling.objects.filter(tenant=request.tenant).first()
    if not tenant_billing_info:
        return Response({'error': 'Tenant billing information not found'}, status=status.HTTP_404_NOT_FOUND
                        )
    invoice = Invoice.objects.filter(tenant_billing=tenant_billing_info, status='pending').order_by("created_at").first()
    print(invoice)
    
    if invoice:
        serializer = InvoiceSerializer(invoice)
        
        return Response({"invoice":serializer.data},status=status.HTTP_200_OK)
    else:
        return Response({"status":False},status=status.HTTP_200_OK)
